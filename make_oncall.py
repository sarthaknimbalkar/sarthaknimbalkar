"""You're on call. It's 2:14am. Playable, in a README, with nothing running.

Same mechanic as the DOOM-in-a-readme port: a directed graph whose nodes are markdown
files and whose edges are hyperlinks. Every state is pre-rendered before it ships, so
there is no engine, no server, no JavaScript, and no state to keep. GitHub's renderer
is a text file viewer, so the whole game is text files.

Moves that don't exist are not links. You cannot brute force out of a wrong theory.

The outage clock is state, which is why several nodes exist three times over: arriving
at the logs at minute 4 is a different state from arriving at minute 14 because you
chased the firewall, or minute 27 because you restarted the fleet first. Duplicating
states instead of computing them is the entire trick.

Difficulty is deliberate. Three separate theories look right and are not. One of the
four available fixes sounds like the textbook answer and does not solve the problem.
Take too long and the decision is taken away from you.

Run: python make_oncall.py   ->   assets/oncall/*.svg + oncall/*.md
"""

import pathlib

W = 840
PAD = 30
LINE_H = 25
FONT = 17.5
BAR_H = 46

# The operator's record. The fastest route the graph allows is computed at build time
# and asserted to be slower than this, so the player can never beat him.
MY_RECORD = 7

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

DARK = dict(ink="#0b0907", chrome="#15110d", fg="#e8ddc9", dim="#8d8171", faint="#5b5344",
            accent="#ffa028", ember="#ff5330", ok="#7ddc7d", hair="#241d16")
LIGHT = dict(ink="#04150b", chrome="#0a2416", fg="#eafff0", dim="#7ba98a", faint="#3d6b4e",
             accent="#3dff8f", ember="#ff5a4d", ok="#c9ff4d", hair="#0f2e1b")

KIND = {"$": "accent", "!": "ember", "+": "ok", " ": "dim", "#": "faint", "*": "fg"}

G = {}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clock(m):
    return f"{2 + (14 + m) // 60}:{(14 + m) % 60:02d} AM"


def affected(m):
    """Blast radius grows while you think. This is the pressure."""
    return 0 if not m else min(4_100 * m + 900, 260_000)


def stakes(m):
    """Escalation lines injected by elapsed time, not authored per node."""
    out = []
    if m >= 12:
        out.append("!#incident-1  @here who owns gateway. answer.")
    if m >= 22:
        out.append("!phone  +1 unknown  ·  a clinic cannot open the medication room")
    if m >= 34:
        out.append("!#incident-1  exec bridge opening. someone is going to ask you to explain.")
    if m >= 46:
        out.append("!status page flipped to MAJOR OUTAGE without you.")
    return out


def frame(node, c):
    lines = list(node["screen"])
    extra = stakes(node["elapsed"]) if not node.get("resolved") else []
    if extra:
        lines = lines + [" "] + extra
    H = BAR_H + PAD + len(lines) * LINE_H + PAD - 6
    el, res = node["elapsed"], node.get("resolved")

    out = [f'<rect width="{W}" height="{H}" rx="8" fill="{c["ink"]}"/>',
           f'<rect width="{W}" height="{BAR_H}" fill="{c["chrome"]}"/>',
           f'<rect y="{BAR_H}" width="{W}" height="1" fill="{c["hair"]}"/>']
    for i, cx in enumerate((PAD, PAD + 19, PAD + 38)):
        out.append(f'<circle cx="{cx}" cy="{BAR_H / 2}" r="5" '
                   f'fill="{(c["ember"], c["accent"], c["ok"])[i]}" opacity="0.85"/>')
    mid = f"{clock(el)}  ·  {'resolved' if res else f'SEV-1  ·  {affected(el):,} users down'}"
    out.append(f'<text x="{W / 2}" y="{BAR_H / 2 + 6}" text-anchor="middle" font-family="{MONO}" '
               f'font-size="15" fill="{c["dim"]}">{mid}</text>')
    out.append(f'<text x="{W - PAD}" y="{BAR_H / 2 + 6}" text-anchor="end" font-family="{MONO}" '
               f'font-size="15" font-weight="700" fill="{c["ok"] if res else c["ember"]}">'
               f'{"RESOLVED" if res else "DOWN"}  {el}m</text>')

    y = BAR_H + PAD + 12
    for ln in lines:
        tag, text = (ln[0], ln[1:]) if ln[:1] in KIND else (" ", ln)
        out.append(f'<text x="{PAD}" y="{y}" font-family="{MONO}" font-size="{FONT}" '
                   f'font-weight="{"700" if tag in "$!" else "400"}" fill="{c[KIND[tag]]}">'
                   f'{esc(text)}</text>')
        y += LINE_H

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
            f'height="{H}" role="img" aria-label="{esc(node.get("alt", "terminal"))}">'
            + "".join(out) + "</svg>")


def node(nid, elapsed, screen, ask=None, moves=(), locked=(), resolved=False, end=None, alt=""):
    G[nid] = dict(id=nid, elapsed=elapsed, screen=screen, ask=ask, moves=list(moves),
                  locked=list(locked), resolved=resolved, end=end, alt=alt)


# ------------------------------------------------------------------ the opening
node("start", 0, [
    "!PAGER  every region  ·  every instance  ·  02:14:07",
    " ",
    " gateway-eu     unreachable",
    " gateway-us     unreachable",
    " gateway-ap     unreachable",
    " ",
    "#not one region. not one box. all of them, in the same second.",
], ask="You are awake. Four things look worth doing. Three of them are wrong.", moves=[
    ("Restart the fleet. Up first, understand later.", "restart", 3),
    ("Check the client's network change log. This happened before.", "firewall", 9),
    ("Check the deploy that shipped two hours ago.", "deploy", 7),
    ("Read the gateway logs.", "logs", 4),
    ("Check whether anything we depend on is down.", "deps", 5),
], alt="Pager alert at 2:14am: every region, every instance unreachable in the same second.")

# ------------------------------------------------------------- decoy 1: restart
node("restart", 3, [
    "$ fleet restart --all",
    " rolling 340 instances ...",
    "+340/340 back up. requests flowing. latency normal.",
    " ",
    "#it worked. you are already typing the all-clear.",
    " ",
    "!02:35  every region  ·  every instance  ·  down again, harder",
], ask="Eleven good minutes, then it died worse than before.", moves=[
    ("Read the gateway logs.", "logs_late", 24),
], locked=[("Restart the fleet again.", "you just watched what that buys you")],
    alt="The restart brings everything back, then everything fails together again, harder.")

# ------------------------------------------------------------ decoy 2: firewall
node("firewall", 9, [
    "$ git log --since=48h -- client/network/",
    " (no commits)",
    "$ curl -sS https://status.client.example/api",
    ' {"incidents": [], "updated": "02:11Z"}',
    " ",
    "#nine minutes spent proving nothing happened.",
], ask="Their side never moved. The theory you walked in with is dead.", moves=[
    ("Read the gateway logs.", "logs_mid", 5),
    ("Check whether anything we depend on is down.", "deps_mid", 6),
], alt="The client's network change log is empty and their status page is clean.")

# -------------------------------------------------------------- decoy 3: deploy
node("deploy", 7, [
    "$ deploys --since 4h",
    " 00:12  gateway v3.19.2   canary 5% -> 100%   clean",
    "$ deploys rollback --dry-run gateway",
    " would revert 1 commit: 'bump timeout 3s -> 5s'",
    " ",
    "#a deploy two hours before an outage is the most tempting lead there is.",
    "#it is also the reason you will lose twelve minutes.",
], ask="A timeout bump. Suspicious, and unrelated. Roll it back anyway?", moves=[
    ("Roll it back. It is the only thing that changed.", "rollback", 12),
    ("Leave it. Read the gateway logs.", "logs_mid", 5),
], alt="A deploy two hours earlier bumped a timeout from three to five seconds.")

node("rollback", 19, [
    "$ deploys rollback gateway --now",
    " reverted to v3.19.1 across 340 instances",
    "!no change. every region still down.",
    " ",
    "#you rolled back the only thing that changed and it did not matter.",
    "#which means the thing that broke us did not change tonight.",
], ask="Nothing changed tonight. So what fired?", moves=[
    ("Read the gateway logs.", "logs_late", 8),
], alt="Rolling back the deploy changes nothing; the cause did not ship tonight.")

# --------------------------------------------------------------- the dependency
node("deps", 5, [
    "$ dep-status --all",
    " auth-store      ok",
    " token-service   ok    (blip 02:13:58, 412ms)",
    " object-store    ok",
    " ",
    "#one dependency hiccuped for four tenths of a second, then recovered.",
    "#we have been down for five minutes and counting.",
], ask="412 milliseconds, recovered. And we are still down. Those facts do not fit yet.", moves=[
    ("Read the gateway logs.", "logs", 3),
], alt="A dependency blipped for 412 milliseconds and recovered while the outage continues.")

node("deps_mid", 20, [
    "$ dep-status --all",
    " token-service   ok    (blip 02:13:58, 412ms)",
    " ",
    "#412 milliseconds, twenty minutes ago, and we are still down.",
    "#something is amplifying it.",
], ask="Something turned four tenths of a second into twenty minutes.", moves=[
    ("Read the gateway logs.", "logs_mid", 2),
], alt="The blip lasted 412ms twenty minutes ago and something is amplifying it.")

# ---------------------------------------- the investigation, at three price tags
LOGS = [
    "$ tail -n 2000 gateway.log | cut -d' ' -f4 | sort | uniq -c | sort -rn | head -3",
    " 1974 POST /v1/session/refresh",
    "   19 GET  /health",
    "    7 POST /v1/session/create",
    " ",
    "#not user traffic. one call, from everywhere, over and over.",
]
STAMPS = [
    "$ grep refresh gateway.log | awk '{print $2}' | uniq -c | head -5",
    "    41 02:13:59.412",
    " 8,806 02:14:00.412",
    " 8,791 02:14:01.412",
    " 8,802 02:14:02.412",
    " 8,795 02:14:03.412",
    " ",
    "*every one of them lands on .412",
    "#eight thousand machines agreeing on a millisecond.",
]
CAUSE = [
    "$ git log -S 'retry' --oneline client/http/ | head -1",
    " 4e1a9c2  make the client resilient to blips  (6 weeks ago)",
    "$ sed -n '19,21p' client/http/retry.py",
    " RETRIES   = 6",
    " BACKOFF_S = 1.0        # fixed",
    " JITTER    = None",
    " ",
    "*blip fails 8,800 clients at once. all six retries land together.",
    "*they fail together, so they retry together, so they fail together.",
]

for tag, add in (("", 0), ("_mid", 10), ("_late", 23)):
    L = lambda base: base + add

    node(f"logs{tag}", L(4), LOGS,
         ask="One endpoint, repeated. Now decide what that means.", moves=[
             ("We are being hammered. Scale up.", f"scale{tag}", 8),
             ("Throttle that endpoint and stop the bleeding.", f"throttle{tag}", 6),
             ("Look at the timestamps.", f"stamps{tag}", 5),
         ], alt="Gateway logs show one endpoint called 1,974 times out of 2,000 requests.")

    node(f"scale{tag}", L(12), [
        "$ fleet scale --replicas 900",
        " 900/900 ready",
        "!queue depth 1.4M and climbing faster than before",
        " ",
        "#more capacity, more clients, more retries. the pile grows.",
    ], ask="Capacity made it worse. That should tell you something about the shape of this.", moves=[
        ("Look at the timestamps.", f"stamps{tag}", 6),
    ], locked=[("Scale up further.", "the queue grew last time")],
        alt="Scaling to 900 replicas makes the queue grow faster.")

    node(f"throttle{tag}", L(10), [
        "$ ratelimit set /v1/session/refresh 200/s",
        "+queue draining  1.4M -> 12k -> 0",
        "+all regions healthy",
        " ",
        "#it is over. you still have no idea what happened.",
    ], ask="Service is up. The cause is untouched.", moves=[
        ("Close the laptop. It is 3am and it is fixed.", "end_bleeding", 2),
        ("Stay up. Find out what actually did this.", f"stamps{tag}", 7),
    ], resolved=True,
        alt="A rate limit restores service without finding the cause.")

    node(f"stamps{tag}", L(9), STAMPS,
         ask="They are not arriving. They are arriving together.", moves=[
             ("Something must be scheduling them. Check cron.", f"cron{tag}", 6),
             ("The load balancer must be batching them.", f"lb{tag}", 5),
             ("Ask who told them all to wake on the same millisecond.", f"cause{tag}", 5),
         ], alt="Every request lands on the same millisecond, 8,800 per second.")

    node(f"cron{tag}", L(15), [
        "$ crontab -l ; kubectl get cronjobs -A | grep -c 02:14",
        " 0",
        " ",
        "#nothing scheduled this. they decided it themselves.",
    ], ask="Nothing scheduled it. They synchronised on their own.", moves=[
        ("Ask who told them all to wake on the same millisecond.", f"cause{tag}", 4),
    ], alt="No scheduled job matches the timing; the clients synchronised themselves.")

    node(f"lb{tag}", L(14), [
        "$ lb config get --key batching",
        " batching: disabled",
        "$ lb stats --window 60s | grep -i coalesce",
        " coalesced: 0",
        " ",
        "#the balancer is forwarding them exactly as it receives them.",
        "#the synchronisation is upstream of us. it is in them.",
    ], ask="Not the balancer. The clients are doing this to us on purpose.", moves=[
        ("Ask who told them all to wake on the same millisecond.", f"cause{tag}", 4),
    ], alt="Load balancer batching is disabled and it coalesced nothing.")

    node(f"cause{tag}", L(14), CAUSE,
         ask="Six weeks ago someone made the client resilient. Four fixes. One works.", moves=[
             ("Switch to exponential backoff.", f"backoff{tag}", 6),
             ("Add random jitter to every retry.", f"end_win{tag}", 5),
             ("Raise capacity permanently so the stampede fits.", "end_bad", 9),
             ("Rip the retries out. They caused this.", "end_fragile", 4),
         ], alt="A six-week-old commit added six retries on a fixed one second backoff, no jitter.")

    node(f"backoff{tag}", L(20), [
        "$ git diff client/http/retry.py",
        "-BACKOFF_S = 1.0        # fixed",
        "+BACKOFF   = 'exponential: 1s, 2s, 4s, 8s ...'",
        "$ deploy --canary 5% && dep-status --replay-blip",
        "!stampede at +1s. then +3s. then +7s. smaller, still synchronised.",
        " ",
        "#exponential backoff spaces out one client's attempts.",
        "#it does not stop eight thousand clients from counting in step.",
    ], ask="The textbook answer, and it only made the stampedes further apart.", moves=[
        ("Add random jitter to every retry.", f"end_win{tag}", 5),
        ("Good enough. Ship it and go to bed.", "end_backoff", 3),
    ], alt="Exponential backoff spaces out the stampedes but keeps them synchronised.")

    node(f"end_win{tag}", L(19), [
        "$ git diff client/http/retry.py",
        " BACKOFF_S = 1.0        # base",
        "+JITTER    = (0.0, 0.9)   # random, per client, per attempt",
        "+BREAKER   = 'open at 30% error, half-open after 5s'",
        "$ deploy --canary 5% && dep-status --replay-blip",
        "+blip replayed. no stampede. queue never exceeded 400.",
        "+all regions healthy.",
        " ",
        "*the outage was 412 milliseconds long.",
        "*the rest of it was us, knocking in unison.",
    ], resolved=True, end="win",
        alt="Adding random jitter and a circuit breaker resolves the outage.")

# --------------------------------------------------------------------- endings
node("end_bad", 0, [
    "$ fleet scale --replicas 2400   # permanent",
    "+queue absorbed. all regions healthy.",
    " ",
    "#the stampede still happens every time. it just fits now.",
    "#it fits until the blip lasts two seconds instead of four tenths,",
    "#and the invoice arrives every month until then.",
], resolved=True, end="bad", alt="Permanently overscaling absorbs the stampede and hides the cause.")

node("end_fragile", 0, [
    "$ git revert 4e1a9c2   # remove retries entirely",
    "+queue 0. all regions healthy.",
    " ",
    "#now a 412ms blip drops 8,800 requests on the floor.",
    "#you traded a stampede for a cliff.",
], resolved=True, end="fragile", alt="Removing retries entirely trades a stampede for dropped requests.")

node("end_backoff", 0, [
    "$ # shipped exponential backoff. 03:4x. laptop closed.",
    " ",
    "#eleven days later, a 900ms blip.",
    "#the stampedes arrive at +1s, +3s, +7s, +15s.",
    "#quieter, in step, and nobody thinks to look at retry.py again",
    "#because retry.py was the thing that got fixed.",
], resolved=True, end="backoff", alt="Exponential backoff without jitter fails again eleven days later.")

node("end_bleeding", 0, [
    "$ # 03:1x, service healthy, laptop closed",
    " ",
    "#the rate limit is still there three weeks later.",
    "#nobody remembers why. someone will clean it up.",
    "#the blip always comes back.",
], resolved=True, end="bleeding", alt="Going to bed after the rate limit leaves the cause in place.")

RULE = "Randomness is a safety feature. Anything that fails together will retry together."

ENDINGS = {
    "win": ("You found it.",
            "A dependency was gone for 412 milliseconds. Everything after that was us: eight "
            "thousand clients that failed on the same instant, and therefore retried on the same "
            "instant, forever. The fix was one line of randomness and one circuit breaker.",
            "Nothing in the logs said stampede. No alert fires on *these timestamps agree too "
            "well*. You got here by asking who told them all to wake up together, and that is not "
            "a command you can run."),
    "backoff": ("You shipped the textbook answer.",
            "Exponential backoff is correct and it is not the fix. It spaces out one client's "
            "attempts. It does nothing about eight thousand clients counting in step with each "
            "other, so the stampedes just move further apart and get quieter.",
            "This is the ending most engineers get, and the dangerous part is that it looks like "
            "a win for eleven days."),
    "bad": ("You paid for it instead.",
            "Capacity hides a stampede the way a bigger bucket hides a leak.",
            "The cause is still sitting in the client on a fixed one second beat, waiting for a "
            "blip long enough to outgrow the bucket you bought."),
    "fragile": ("You traded one failure for another.",
            "With no retries at all, that 412ms blip drops eight thousand requests instead of "
            "amplifying them.",
            "Retrying was the right instinct. Retrying in unison was the bug. You threw out the "
            "instinct and kept the lesson backwards."),
    "bleeding": ("You stopped the bleeding.",
            "Which is the correct first move, and it is not the job.",
            "The rate limit will outlive everyone's memory of why it exists. That is precisely "
            "how this comes back."),
}


def write(svg_dir, md_dir):
    for nid, n in G.items():
        (svg_dir / f"{nid}-dark.svg").write_text(frame(n, DARK), encoding="utf-8")
        (svg_dir / f"{nid}-light.svg").write_text(frame(n, LIGHT), encoding="utf-8")

        md = ["<!-- Generated by make_oncall.py. Every state in this game is a file. -->", "",
              "<picture>",
              f'  <source media="(prefers-color-scheme: dark)" srcset="../assets/oncall/{nid}-dark.svg">',
              f'  <source media="(prefers-color-scheme: light)" srcset="../assets/oncall/{nid}-light.svg">',
              f'  <img alt="{n["alt"]}" src="../assets/oncall/{nid}-dark.svg" width="100%">',
              "</picture>", ""]

        if n["end"]:
            title, what, why = ENDINGS[n["end"]]
            md += [f"### {title}", "", what, "", why, "", f"**{RULE}**", ""]
            if n["elapsed"]:
                md.append(f"**You: {n['elapsed']} minutes.**  ·  **Me: {MY_RECORD} minutes.**  "
                          f"That is the record and it is not close. The fastest route this thing "
                          f"allows is {FASTEST} minutes, so you were never going to catch me.")
            else:
                md.append(f"**Me: {MY_RECORD} minutes**, the night I found it, on the first pass, "
                          f"without a rate limit and without restarting anything.")
            md += ["", "[Take the page again](./start.md) · "
                       "[I write these down](https://sarthaknimbalkar.in/) · "
                       "[Back to the profile](../)", ""]
        else:
            md += [f"**{n['ask']}**", ""]
            for label, target, _c in n["moves"]:
                md.append(f"- [{label}](./{target}.md)")
            for label, reason in n["locked"]:
                md.append(f"- ~~{label}~~ <sub>{reason}</sub>")
            md += ["", f"<sub>{n['elapsed']} minutes down · {affected(n['elapsed']):,} users out · "
                       f"no JavaScript is running. Every move is a different file in "
                       f'<a href="../oncall/">this folder</a>.</sub>', ""]

        (md_dir / f"{nid}.md").write_text("\n".join(md), encoding="utf-8")


def fastest_win():
    """Cheapest reachable win, so the record can be asserted unbeatable."""
    best, stack = None, [("start", 0, {"start"})]
    while stack:
        nid, cost, seen = stack.pop()
        n = G[nid]
        if n["end"] == "win":
            best = cost if best is None else min(best, cost)
            continue
        for _l, t, c in n["moves"]:
            if t not in seen:
                stack.append((t, cost + c, seen | {t}))
    return best


FASTEST = None

if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    svg_dir, md_dir = here / "assets" / "oncall", here / "oncall"
    for d in (svg_dir, md_dir):
        d.mkdir(parents=True, exist_ok=True)
    for old in list(svg_dir.glob("*.svg")) + list(md_dir.glob("*.md")):
        old.unlink()

    holes = [(n["id"], t) for n in G.values() for _l, t, _c in n["moves"] if t not in G]
    assert not holes, f"dangling links: {holes}"

    win_nodes = [n["elapsed"] for n in G.values() if n["end"] == "win"]
    FASTEST = min(win_nodes)
    assert FASTEST > MY_RECORD, f"player could tie or beat the record ({FASTEST} vs {MY_RECORD})"

    write(svg_dir, md_dir)
    ends = sum(1 for n in G.values() if n["end"])
    print(f"{len(G)} states · {ends} endings · {len(G) * 2} frames · all links resolve")
    print(f"fastest possible win: {FASTEST}m · operator record: {MY_RECORD}m (unbeatable)")
    print(f"decoys: restart, firewall, deploy+rollback, cron, load balancer, exponential backoff")
