# Pacman-Mirror
Final Project: Mirrored Pacman

Introduction to Artificial Intelligence, Spring 2017, National Chiao Tung University


## Techniques & Approaches

Since computational resource is extremely limited, I opted for computationally-cheaper approaches.

- Clear role distribution (not enough resource to evaluate the complexity of role switching)
- An advanced evaluation function that accounts for various factors
- Depth-limited search to evaluate safety
- Stall checking with sliding window (kind of lousy due to countermeasures against TA's bug)

Please refer to [`30_SmileOuO.py`](30_SmileOuO.py)

## Commands

`##_TeamName = 30_SmileOuO`

```
python capture.py
-r [##_TeamName]: Load the red team
-b [##_TeamName]: Load the blue team
-l [Layout]: Load another layout
-c: Catch exceptions and enforce time limits
-n #: Play # games
-q: quiet mode, no graphics
-z: layout size
-i: execution time(default 1800)
--keys0: control the first agent of red with keyboard
--keys1: control the first agent of blue with keyboard
First: WASD, Second: IJKL
```
