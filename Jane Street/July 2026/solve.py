"""
Grid: 8x8, tiled by 12 pentominoes + one 2x2 tetromino (13 regions).
A tower (extra cube, altitude 1) sits on exactly one square of each region.
A 3D knight starts at (7,0) with score 0 and makes moves whose displacement
(|dr|,|dc|,|dalt|) is a permutation of (0,1,2). alt in {0,1}, so:
  - flat (1,2)-knight move: dalt=0, endpoints same tower-status  -> score += N
  - up   (2,0)/(0,2) move : flat -> tower                        -> score *= N
  - down (2,0)/(0,2) move : tower -> flat (needs divisibility)   -> score /= N
Knight visits all 13 towers, never repeats a square, stops at 13th tower.
Recorded scores at moves 0,3,6,9,12,15,18 then every K>3 moves.
"""

# ---- region reconstruction from detected walls (7=wall, 2=open) ----
h = {1:[7,7,7,7,7,7,7,2],2:[2,7,2,2,2,7,2,2],3:[7,2,7,7,7,7,2,7],
     4:[2,7,2,2,2,2,7,7],5:[2,7,2,7,7,2,7,2],6:[2,2,7,2,7,7,2,2],7:[7,2,7,2,7,2,7,2]}
v = {1:[2,2,7,7,2,7,7,2],2:[2,2,7,2,7,7,7,2],3:[2,7,7,7,7,7,2,7],
     4:[2,2,2,2,2,7,2,7],5:[7,7,2,7,7,2,7,2],6:[2,2,7,7,2,7,2,7],7:[2,7,7,2,7,7,7,2]}

parent={}
def find(x):
    while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
    return x
def union(a,b): parent[find(a)]=find(b)
for r in range(8):
    for c in range(8): parent[(r,c)]=(r,c)
for bi in range(1,8):
    for c in range(8):
        if h[bi][c]<=3: union((bi-1,c),(bi,c))
for bi in range(1,8):
    for r in range(8):
        if v[bi][r]<=3: union((r,bi-1),(r,bi))
labels={}; region=[[0]*8 for _ in range(8)]; nxt=0
for r in range(8):
    for c in range(8):
        root=find((r,c))
        if root not in labels: labels[root]=chr(ord('A')+nxt); nxt+=1
        region[r][c]=labels[root]

REGIONS = sorted(set(labels.values()))
NUMS = {(0,5):37,(0,7):1100,(2,3):23,(2,5):138,(3,0):528,(4,1):449,
        (4,4):16,(5,1):750,(5,3):88,(5,5):272,(5,6):1,(7,0):0}

KNIGHT = [(-1,-2),(-1,2),(1,-2),(1,2),(-2,-1),(-2,1),(2,-1),(2,1)]
ORTHO2 = [(-2,0),(2,0),(0,-2),(0,2)]
NUMSET = set(NUMS)
START = (7,0)
SCORE_CAP = 10**7
solutions = []

def inb(r,c): return 0<=r<8 and 0<=c<8

def dfs(pos, alt, n, score, visited, towers, region_flat, K, post18, path):
    """post18 = list of moves>18 where we recorded (landed on numbered sq)."""
    # ---- record-move / numbered-square consistency for the square we just arrived at ----
    numbered = pos in NUMSET
    if 1 <= n <= 18:
        if n % 3 == 0:
            if not numbered or score != NUMS[pos]:
                return
        else:
            if numbered:
                return
    elif n > 18:
        if numbered:
            # this arrival is a recording; check spacing
            if score != NUMS[pos]:
                return
            if K is None:
                k = n - 18
                if k < 4:            # K must be strictly larger than 3
                    return
                K = k
                post18 = post18 + [n]
            else:
                if n != 18 + K*(len(post18)+1):
                    return
                post18 = post18 + [n]
            if len(post18) > 5:
                return
        else:
            # not numbered: must not coincide with an expected recording move
            if K is not None and (n-18) % K == 0:
                return

    # ---- termination: all 13 towers visited ----
    if len(towers) == 13:
        # need every numbered square recorded: 6 at moves 3..18 + 5 post18
        if len(post18) == 5:
            solutions.append(list(path))
        return

    if score > SCORE_CAP:
        return

    N = n + 1  # number of the move we are about to make
    # branch over flat knight moves (same altitude)
    for dr,dc in KNIGHT:
        nr,nc = pos[0]+dr, pos[1]+dc
        if not inb(nr,nc): continue
        if (nr,nc) in visited: continue
        nscore = score + N
        _try(nr,nc,alt,N,nscore,visited,towers,region_flat,K,post18,path)
    # branch over vertical moves (altitude changes by 1)
    for dr,dc in ORTHO2:
        nr,nc = pos[0]+dr, pos[1]+dc
        if not inb(nr,nc): continue
        if (nr,nc) in visited: continue
        nalt = 1-alt
        if nalt==1:  # up: multiply
            nscore = score * N
        else:        # down: divide (must be exact)
            if score % N != 0: continue
            nscore = score // N
        _try(nr,nc,nalt,N,nscore,visited,towers,region_flat,K,post18,path)

def _try(nr,nc,nalt,N,nscore,visited,towers,region_flat,K,post18,path):
    reg = region[nr][nc]
    towers2 = towers
    region_flat2 = region_flat
    if nalt==1:
        if reg in towers: return          # region already has its tower
        towers2 = dict(towers); towers2[reg] = (nr,nc)
    else:
        # mark flat; check the region can still get a tower somewhere
        region_flat2 = dict(region_flat)
        region_flat2[reg] = region_flat2.get(reg,0)+1
    visited.add((nr,nc)); path.append((nr,nc,nalt,nscore))
    dfs((nr,nc), nalt, N, nscore, visited, towers2, region_flat2, K, post18, path)
    visited.discard((nr,nc)); path.pop()

# ============ PHASE 1: enumerate valid prefixes up to move 18 ============
prefixes = []  # each: (path, towers, K_none)

def step18(nr,nc,nalt,N,nscore,visited,towers,path):
    reg = region[nr][nc]
    added = False
    if nalt==1:                      # landing on a tower square (up-move OR flat-at-alt1)
        if reg in towers: return
        towers[reg] = (nr,nc); added = True
    visited.add((nr,nc)); path.append((nr,nc,nalt,nscore))
    dfs18((nr,nc), nalt, N, nscore, visited, towers, path)
    visited.discard((nr,nc)); path.pop()
    if added: del towers[reg]

def dfs18(pos, alt, n, score, visited, towers, path):
    numbered = pos in NUMSET
    if 1 <= n <= 18:
        if n % 3 == 0:
            if not numbered or score != NUMS[pos]:
                return
        else:
            if numbered:
                return
    if n == 18:
        prefixes.append((list(path), dict(towers)))
        return
    if score > SCORE_CAP:
        return
    N = n + 1
    for dr,dc in KNIGHT:                       # flat move: altitude unchanged
        nr,nc = pos[0]+dr, pos[1]+dc
        if not inb(nr,nc) or (nr,nc) in visited: continue
        step18(nr,nc,alt,N,score+N,visited,towers,path)
    for dr,dc in ORTHO2:                        # vertical move: altitude flips
        nr,nc = pos[0]+dr, pos[1]+dc
        if not inb(nr,nc) or (nr,nc) in visited: continue
        nalt = 1-alt
        if nalt==1:
            step18(nr,nc,nalt,N,score*N,visited,towers,path)
        else:
            if score % N != 0: continue
            step18(nr,nc,nalt,N,score//N,visited,towers,path)

def sol_K(sol):
    recs = [i for i in range(19,len(sol)) if (sol[i][0],sol[i][1]) in NUMSET]
    return recs[0]-18 if recs else -1

# ============ PHASE 2 (fixed K): extend a move-18 prefix ============
solK = []
def dfsK(pos, alt, n, score, visited, towers, region_flat, K, nrec, path):
    if n > 18:
        numbered = pos in NUMSET
        if (n-18) % K == 0:
            i = (n-18)//K
            if i > 5 or not numbered or score != NUMS[pos]:
                return
            nrec = i
        else:
            if numbered:
                return
    if len(towers) == 13:
        if nrec == 5:
            solK.append(list(path))
        return
    if score > SCORE_CAP:
        return
    if n >= 18 + 6*K:      # depth bound: tail after last recording is < K moves
        return
    N = n + 1
    for dr,dc in KNIGHT:
        nr,nc = pos[0]+dr, pos[1]+dc
        if not inb(nr,nc) or (nr,nc) in visited: continue
        _tryK(nr,nc,alt,N,score+N,visited,towers,region_flat,K,nrec,path)
    for dr,dc in ORTHO2:
        nr,nc = pos[0]+dr, pos[1]+dc
        if not inb(nr,nc) or (nr,nc) in visited: continue
        nalt = 1-alt
        if nalt==1:
            _tryK(nr,nc,nalt,N,score*N,visited,towers,region_flat,K,nrec,path)
        else:
            if score % N != 0: continue
            _tryK(nr,nc,nalt,N,score//N,visited,towers,region_flat,K,nrec,path)

def _tryK(nr,nc,nalt,N,nscore,visited,towers,region_flat,K,nrec,path):
    reg = region[nr][nc]
    added=False
    if nalt==1:
        if reg in towers: return
        towers[reg]=(nr,nc); added=True
    else:
        # if this fills the region entirely with flats and it still has no tower -> dead
        pass
    visited.add((nr,nc)); path.append((nr,nc,nalt,nscore))
    dfsK((nr,nc), nalt, N, nscore, visited, towers, region_flat, K, nrec, path)
    visited.discard((nr,nc)); path.pop()
    if added: del towers[reg]

if __name__ == "__main__":
    import sys
    sys.setrecursionlimit(10000)
    for a0 in (0,1):
        vis = {START}
        tw = {}
        p = [(START[0],START[1],a0,0)]
        if a0==1:
            tw[region[7][0]] = START
        dfs18(START, a0, 0, 0, vis, tw, p)
    print("phase-1 prefixes (to move 18):", len(prefixes))
    chk = [(prefixes[0][0][i][0],prefixes[0][0][i][1],prefixes[0][0][i][3]) for i in (3,6,9,12,15,18)]
    print("forced checkpoints (move,sq,score):", chk)

    # ============ PHASE 2: extend each prefix for each fixed K ============
    for K in range(4, 12):
        for path, tw in prefixes:
            visited = set((r,c) for (r,c,a,s) in path)
            towers = dict(tw)
            region_flat = {}
            pos = (path[-1][0], path[-1][1]); alt = path[-1][2]; score = path[-1][3]
            dfsK(pos, alt, 18, score, visited, towers, region_flat, K, 0, list(path))
        print("K=%d cumulative solutions: %d" % (K, len(solK)), flush=True)

    # dedupe solutions
    uniq = []
    seen = set()
    for sol in solK:
        key = tuple((r,c) for (r,c,a,s) in sol)
        if key in seen: continue
        seen.add(key); uniq.append(sol)
    print("solutions found:", len(solK), "unique paths:", len(uniq))
    for sol in uniq[:8]:
        print("=== length %d moves, K=%d ===" % (len(sol)-1, sol_K(sol)))
        for i,(r,c,alt,sc) in enumerate(sol):
            tag = "  <== REC %d" % NUMS[(r,c)] if (r,c) in NUMSET else ""
            print(f"  move {i:2d}: ({r},{c}) alt{alt} score={sc}{tag}")

    # ============ FINAL ANSWER ============
    assert len(uniq)==1, "not unique!"
    sol = uniq[0]
    score_at = {(r,c):sc for (r,c,alt,sc) in sol}
    towers = {(r,c) for (r,c,alt,sc) in sol if alt==1}
    visited = set(score_at)
    print("\nvisited squares:", len(visited), " towers:", len(towers))
    # check one tower per region
    from collections import Counter
    treg = Counter(region[r][c] for (r,c) in towers)
    assert all(v==1 for v in treg.values()) and len(treg)==13, treg

    unvisited = [(r,c) for r in range(8) for c in range(8) if (r,c) not in visited]
    print("unvisited squares:", len(unvisited), sorted(unvisited))

    total = 0
    details=[]
    for (r,c) in unvisited:
        s = 0
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr,nc = r+dr, c+dc
            if 0<=nr<8 and 0<=nc<8 and (nr,nc) in visited:
                s += score_at[(nr,nc)]
        details.append(((r,c), s))
        total += s
    print("\nneighbor sums per unvisited square:")
    for (sq,s) in details:
        print("   ", sq, "->", s)
    print("\n*** FINAL ANSWER (sum of neighbor sums) =", total, "***")

    # dump grids for the writeup
    print("\nScore grid (visited squares):")
    for r in range(8):
        row=[]
        for c in range(8):
            if (r,c) in score_at:
                mark="T" if (r,c) in towers else " "
                row.append("%6d%s"%(score_at[(r,c)],mark))
            else:
                row.append("     . ")
        print(" ".join(row))
    print("\nMove-order grid:")
    order={(r,c):i for i,(r,c,a,s) in enumerate(sol)}
    for r in range(8):
        print(" ".join(("%3d"%order[(r,c)]) if (r,c) in order else "  ." for c in range(8)))
