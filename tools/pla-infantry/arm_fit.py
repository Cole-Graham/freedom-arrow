"""Fit source arm landmarks to the unchanged native skeleton.

The SF equipment sheet has no skeleton. It uses the regular source's rest-pose
landmarks as a starting cage; its visual fit still requires native review.
"""
import numpy as np


class ArmFit:
    def __init__(self, source, native, body_height):
        self.sides = []
        self.audit = []
        for suffix, side, sign in [('l', 'Left', 1), ('r', 'Right', -1)]:
            pairs = [('upperarm_'+suffix, side+'Arm'),
                     ('lowerarm_'+suffix, side+'ForeArm'),
                     ('hand_'+suffix, side+'Hand')]
            for source_finger, native_finger in [('index', 'Index'), ('ring', 'Ring'), ('thumb', 'Thumb')]:
                pairs += [(f'{source_finger}_0{i}_{suffix}', f'{side}Hand{native_finger}{i}') for i in range(1, 4)]
            src = [source[s] for s, _ in pairs]
            # Match the loader's offset taper. Hands/fingers use their native
            # bones with zero displacement so grips do not drift as poses rotate.
            def offset_scale(name):
                return 0 if 'Hand' in name else .35 if 'ForeArm' in name else .75
            dst = [np.asarray(native[n]) - [0, 0, body_height*offset_scale(n)] for _, n in pairs]
            for x, y, z in [(0.08, 0, 1.50), (0.12, -.18, 1.35), (.12, .18, 1.35), (.20, 0, .86)]:
                q = np.array([sign*x, y, z])
                src.append(q); dst.append(q)
            src, dst = np.asarray(src), np.asarray(dst)
            center = src.mean(axis=0); scale = .5
            cage = (src-center)/scale
            poly = np.column_stack([np.ones(len(cage)), cage])
            radius = np.linalg.norm(cage[:, None, :]-cage[None, :, :], axis=2)
            system = np.block([[radius**3, poly], [poly.T, np.zeros((4, 4))]])
            rhs = np.vstack([dst-src, np.zeros((4, 3))])
            coefficients = np.linalg.solve(system, rhs)
            self.sides.append((sign, cage, center, scale, coefficients))
            fitted = src + np.column_stack([radius**3, poly]) @ coefficients
            error = np.linalg.norm(fitted-dst, axis=1)
            assert np.max(error) < 1e-6, error
            self.audit.append({'side':side, 'landmarks':len(pairs),
                               'max_cage_error_m':float(np.max(error)),
                               'body_height_compensated_m':body_height,
                               'native_hand_offset_m':0})

    def deform(self, points):
        result = np.asarray(points).copy()
        for sign, cage, center, scale, coefficients in self.sides:
            select = (sign*points[:, 0] > .16) & (points[:, 2] > .86)
            q = points[select]
            if not len(q): continue
            norm = (q-center)/scale
            radius = np.linalg.norm(norm[:, None, :]-cage[None, :, :], axis=2)
            delta = np.column_stack([radius**3, np.ones(len(q)), norm]) @ coefficients
            # Blend into the fixed torso and lower arm boundary smoothly.
            blend = np.clip((sign*q[:, 0]-.16)/.10, 0, 1)
            blend *= np.clip((q[:, 2]-.86)/.10, 0, 1)
            blend = blend*blend*(3-2*blend)
            result[select] += delta*blend[:, None]
        assert np.isfinite(result).all()
        return result
