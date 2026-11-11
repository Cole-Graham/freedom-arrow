import unittest
from retention import plan_drive
FOLDER='1bphWHVjwoVTGzXSfwJj7f5jAT6UdzfTw'
def item(id,name,created='2026-11-10T00:00:00Z',folder=FOLDER):return {'id':id,'name':name,'createdTime':created,'parents':[folder]}
class RetentionTests(unittest.TestCase):
 def test_latest_two_and_lock(self):
  rows=[item(str(n),f'FreedomArrow-0.7.0-dev.{n}.bamod') for n in [40,44,45,47]]
  p=plan_drive(rows,{'44'},set());self.assertEqual({x['id'] for x in p['keep']},{'44','45','47'});self.assertEqual([x['id'] for x in p['remove']],['40'])
 def test_asset_dependency(self):
  rows=[item(str(n),f'FreedomArrow-Assets-0.1.{n}.bamod') for n in [12,14,16,17]]
  p=plan_drive(rows,{'14'},set());self.assertEqual({x['id'] for x in p['keep']},{'14','16','17'})
 def test_pla_prototypes_are_older_than_test_builds(self):
  rows=[item('legacy','FreedomArrow-0.6.0-pla.48.bamod'),item('old','PLA-TEST-Build-1.bamod'),item('current','PLA-TEST-Build-2.bamod')]
  self.assertEqual([x['id'] for x in plan_drive(rows,set(),set())['remove']],['legacy'])
 def test_unrelated_and_unrecognized_never_removed(self):
  rows=[item('private','FreedomArrow-0.7.0-dev.1.bamod',folder='outside'),item('note','notes.txt'),item('unknown','FreedomArrow-special.bamod')]
  p=plan_drive(rows,set(),set());self.assertEqual(p['remove'],[]);self.assertEqual([x['id'] for x in p['unknown']],['unknown'])
 def test_latest_duplicate_prefers_newest_unlinked(self):
  rows=[item('old','FreedomArrow-0.7.0-dev.45.bamod','2026-11-09'),item('new','FreedomArrow-0.7.0-dev.45.bamod','2026-11-10')]
  p=plan_drive(rows,set(),set());self.assertEqual([x['id'] for x in p['keep']],['new']);self.assertEqual([x['id'] for x in p['remove']],['old'])
 def test_pinned_name_is_protected(self):
  rows=[item(str(n),f'PLA-TEST-Build-{n}.bamod') for n in [1,4,5,6]]
  p=plan_drive(rows,set(),{'PLA-TEST-Build-4.bamod'});self.assertEqual({x['id'] for x in p['keep']},{'4','5','6'})
if __name__=='__main__':unittest.main()
