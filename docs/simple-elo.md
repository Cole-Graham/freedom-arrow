# Simple Elo

A team starts at 1000. A match moves both ratings by standard Elo. A win below 1500 also adds a bonus, so early results put rating into the pool until teams sit around 1500. The rating after the match selects a grade. The grade boundaries are the old 1500–2170 cuts, stretched so that 1500 lands on 1000 and 2170 stays 2170.

## Constants

| Constant | Value |
| --- | ---: |
| Starting rating | 1000 |
| K-factor | 40 |
| Elo divisor | 400 |
| Minimum rating | 600 |
| Bonus target | 1700 |
| Bonus dead zone | 200 |
| Bonus cap | 1.0 |

The dead zone is what makes the bonus stop at 1500. A winner at 1500 is 200 below the target, and the bonus is 0 for every rating inside that distance.

## Match update

For the winner, the expected score is

```text
expected = 1 / (1 + 10 ^ ((loserRating - winnerRating) / 400))
base = 40 × (1 - expected)
```

The loser is the mirror of that base. The winner then receives the bonus:

```text
winnerChange = base × (1 + bonus)
loserChange = -base
```

Each new rating is kept at 600 or above.

`bonus` is computed from the winner's rating before the match:

```text
distance = 1700 - winnerRating
bonus = 0                                              when distance <= 200
bonus = 1 - e ^ (-distance / 100)                      otherwise
```

`100` is half the dead zone. The bonus is about 1 at the 1000 start, so a win there is about twice the base change, and it falls to 0 at 1500. A loss never receives it. Two teams at the same rating therefore exchange 20 points once both are at or above 1500, and the winner takes almost 40 from a 20-point base while still under 1500. The extra points stay in the pool. That is what lifts a field that starts at 1000 toward an average around 1500. Past 1500 the exchange is zero-sum, apart from the floor at 600.

| Winner before | Bonus | Base at equal ratings | Winner change | Loser change |
| ---: | ---: | ---: | ---: | ---: |
| 1000 | 0.999 | 20 | +39.98 | −20 |
| 1200 | 0.993 | 20 | +39.87 | −20 |
| 1400 | 0.950 | 20 | +39.00 | −20 |
| 1500 | 0 | 20 | +20 | −20 |
| 1700 | 0 | 20 | +20 | −20 |

Unequal ratings use the same rule. A team at 1400 that beats a team at 1500 has expected score 0.360, so the base is 25.60. The bonus at 1400 is 0.950, and the winner gains `25.60 × 1.950 = 49.93`. The loser drops 25.60. A team at 1600 that beats a team at 1500 has no bonus: expected score 0.640, base 14.40, winner +14.40, loser −14.40.

## Grades

Grades were cut on a scale from 1500 to 2170. Those cuts are mapped onto the scale that starts at 1000:

```text
rescaled = floor(1000 + (original - 1500) × (2170 - 1000) / (2170 - 1500))
```

1500 maps to 1000. 2170 stays 2170. The grade is chosen from the floor of the stored rating.

Private is every rating through 1000, so a new team is a Private. Each later grade starts at its rescaled cut and runs through the next cut minus 1. Lieutenant-General starts at 2170.

| Grade | Original cut | Rating |
| --- | ---: | --- |
| Private | 1500 | 0–1000 |
| Corporal | 1501 | 1001–1035 |
| Sergeant | 1521 | 1036–1077 |
| Sergeant Major | 1545 | 1078–1129 |
| Second Lieutenant | 1575 | 1130–1192 |
| Lieutenant | 1611 | 1193–1267 |
| Captain | 1654 | 1268–1358 |
| Major | 1706 | 1359–1467 |
| Lieutenant-Colonel | 1768 | 1468–1596 |
| Colonel | 1842 | 1597–1753 |
| Brigadier-General | 1932 | 1754–1941 |
| Major-General | 2040 | 1942–2169 |
| Lieutenant-General | 2170 | 2170 and above |

At 2170 and above, leaderboard place replaces the grade for the top three. Place 1 is Field Marshal. Places 2 and 3 are General. Every other team at that rating stays Lieutenant-General.
