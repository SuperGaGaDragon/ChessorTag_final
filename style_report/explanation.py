"""
Single-source tag explanations for front-end tooltips.
Each value should be a concise single sentence.
"""

TAG_EXPLANATIONS = {
    # Maneuver
    "Constructive maneuver": "Reroute that improves piece harmony and future activity.",
    "Constructive maneuver (prepare)": "Quiet reroute that sets up a later plan or breakthrough.",
    "Neutral maneuver": "Repositioning with limited impact—neither improves nor harms much.",
    "Misplaced maneuver": "Reroute that wastes time or worsens coordination.",
    "Opening maneuver": "Early-game reroute to better squares after initial development.",
    "Overall maneuver ratio": "Share of moves classified as maneuvers.",
    # Prophylaxis
    "Direct prophylactic": "Move that directly stops the opponent’s immediate threat or plan.",
    "Latent prophylactic": "Restricts future ideas before they become concrete threats.",
    "Meaningless prophylactic": "Prophylaxis that addresses no real threat.",
    "Failed prophylactic": "Attempted prevention that still allows the threat.",
    "Overall prophylaxis ratio": "Share of moves aimed at prevention.",
    # Semantic control
    "Control: simplify": "Trades or simplifications to reduce complexity.",
    "Control: plan kill": "Stops the opponent’s main strategic plan.",
    "Control: freeze/bind": "Limits opponent mobility and counterplay.",
    "Control: blockade passed pawn": "Holds back or fixes a passed pawn.",
    "Control: file seal": "Secures or contests an open/semi-open file.",
    "Control: king safety shell": "Strengthens the king’s pawn and square cover.",
    "Control: space clamp": "Claims key squares to restrict counterplay.",
    "Control: regroup/consolidate": "Re-coordinates pieces after operations.",
    "Control: slowdown": "Tempers the position to avoid sharp forcing lines.",
    "Overall semantic control ratio": "Share of moves aimed at positional control.",
    # Control over dynamics
    "Control over dynamics (overall)": "Moves chosen to shape the game’s tactical temperature.",
    "CoD: file seal": "Dynamic control by contesting files before tactics explode.",
    "CoD: freeze/bind": "Dynamic restriction to keep the opponent cramped.",
    "CoD: king safety": "Dynamic tweaks that keep the king safe during tactics.",
    "CoD: regroup/consolidate": "Dynamic re-coordination to stabilize.",
    "CoD: plan kill": "Dynamic strike that halts opponent initiative.",
    "CoD: blockade passed pawn": "Dynamic blockading of a passed pawn in sharp play.",
    "CoD: simplify": "Trades to cool down complications.",
    "CoD: space clamp": "Dynamic space grab to limit enemy breaks.",
    "CoD: slowdown": "Tempo moves to cool the position.",
    # Initiative
    "Initiative attempt": "Actively driving threats to keep the move-by-move pressure.",
    "Deferred initiative": "Postpones attack to finish prep or development.",
    "Premature attack": "Attack launched before position is ready.",
    "C-file pressure": "Initiative built around control of the c-file.",
    # Tension
    "Tension creation": "Creates or sustains pawn/piece tension.",
    "Neutral tension creation": "Tension that neither helps nor harms notably.",
    # Structural
    "Structural integrity": "Keeps pawn structure healthy and flexible.",
    "Structural compromise (dynamic)": "Accepts structural weakness for activity.",
    "Structural compromise (static)": "Weak structure without clear compensation.",
    # Sacrifice
    "Tactical sacrifice": "Material given for concrete tactical gain.",
    "Positional sacrifice": "Material invested for long-term positional edge.",
    "Inaccurate tactical sacrifice": "Dubious sac without enough payoff.",
    "Speculative sacrifice": "High-risk sac with unclear compensation.",
    "Desperate sacrifice": "Last-ditch sac from a bad position.",
    "Tactical combination sacrifice": "Sac as part of a forcing combination.",
    "Tactical initiative sacrifice": "Sac to keep initiative flowing.",
    "Positional structure sacrifice": "Material for structural damage to opponent.",
    "Positional space sacrifice": "Material for space or central control.",
    "Overall sacrifice ratio": "Share of moves involving sacrifices.",
    # Exchanges / forced / positions
    "Accurate knight/bishop exchange": "Trade that improves your minor-piece balance.",
    "Inaccurate knight/bishop exchange": "Trade that hands the opponent better minors.",
    "Bad knight/bishop exchange": "Clearly harmful minor-piece trade.",
    "Total exchange frequency": "All tagged minor-piece exchanges.",
    "Forced moves": "Moves compelled by tactics to avoid big loss.",
    "Winning position handling": "Technique in converting clearly winning spots.",
    "Losing position handling": "Resilience when position is bad.",
    # Tactics
    "Tactical opportunities found": "Tactics spotted and exploited.",
    "Tactical opportunities missed": "Tactics available but not taken.",
    "Tactical conversion rate": "Share of tactics you convert.",
}
