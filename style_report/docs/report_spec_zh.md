棋手研究报告（请全部使用英文）

该网站全部在html中出现
由于标签的一些待完善性，LLM解释时不应该只看概率。而应该和其他棋手做比对。比如：control_over_dynamic标签棋手出现概率为40%，但是彼得罗相是60%，塔尔是30%。你不应该说他是控制流棋手，而应该结合其他棋手做出比对。
LLM解读时应该尽可能从这些标签数据中挖取所有的细节并分析，越详细越好。





I：个人能力评估

一、胜率

执白胜率｜执白输率｜执白和率｜对手平均等级分

执黑胜率｜执黑输率｜执黑和率｜对手平均等级分


二、水平参数

1、精确度体系（表格）：

棋手精确度｜同龄棋手精确度｜顶尖棋手精确度｜
总体精确度- 
开局精确度-
中局精确度-
残局精确度-
有后局面精确度-
无后局面精确度-

“点击“顶尖棋手”后，弹出不同棋手的名字，会出现我们预设的数据

2、优势处理能力

执白时｜执黑时
对局出现+1的局面时，获得最终胜/负/和的对局比例：
对局出现+3的局面时，获得最终胜/负/和的对局比例：
对局出现+3的局面时，获得最终胜/负/和的对局比例：
对局出现+7的局面时，获得最终胜/负/和的对局比例：








3、劣势防守能力

执白时｜执黑时
对局出现-1的局面时，获得最终胜/负/和的对局比例：
对局出现-3的局面时，获得最终胜/负/和的对局比例：
对局出现-3的局面时，获得最终胜/负/和的对局比例：
对局出现-7的局面时，获得最终胜/负/和的对局比例：


4、对局走向

执白时｜执黑时
速胜对局占比（全程压制对手）：
速败对局占比（全程被压制）：
小波澜对局占比（2个左右+1到-1以上的起伏）：
起伏对局占比（2个左右+2到-2以上的起伏）：
大起伏对局占比（4个左右+2到-2以上的起伏）
高精度和棋对局占比（没有大于+-0.8的起伏）：


5、不同招法对比：

执白时｜执黑时
Best moves（引擎top2）：
inaccuracies（引擎评分下降0.5以上）
Mistakes（引擎评分下降1以上）
Blunders（引擎评分下降3以上）


6、战术能力

执白时｜执黑时
抓住的战术机会占比：
错过的战术机会占比：


7、其他水平参数

标签名称｜棋手出现次数｜棋手出现概率｜顶尖棋手出现频率
Accurate Knight/Bishop Exchange｜｜｜
Inaccurate Knight/Bishop Exchange｜｜｜
Bad Knight/Bishop Exchange｜｜｜
总体出现概率

LLM解读：“你是一个专业的国际象棋教练，请你a）计算总体出现马象交换局面次数，解释马象交换走法多少意味着什么 b）只根据数据表格，分析三个标签出现概率能反映出的棋手风格和能力 c）评估该棋手和与该棋手数据最接近的顶尖棋手的比对分析”

标签名称｜棋手出现次数｜棋手出现概率｜顶尖棋手出现频率
forced moves｜｜｜

LLM解读：“你是一个专业的国际象棋教练，请你向你的学生 a）解释forced move出现的概率代表棋手经常喜欢什么变化 b）评估forced moves出现频率和该棋手最接近的顶尖棋手”


8、胜败局面统计
该标签家族统计该棋手出现的胜势/败势局面。棋手水平高，则该标签更加精确（低水平棋手常有败势不认输的情况，会严重污染此标签）

标签名称｜棋手出现次数｜棋手出现概率｜顶尖棋手出现频率｜解读
Winning position handling｜｜｜｜该数据越多，则棋手进攻更加犀利
Losing position handling ｜｜｜｜

LLM解读：你是一个专业国际象棋教练。请你：
A）分析两个标签的比例结构，评估该棋手风格。b)评估该棋手和与该棋手数据最渐进的顶尖棋手的比对分析。注意：如果该棋手数据超过频率最高的顶级棋手的1倍以上，则输出数据没有参考价值。
要求：不要根据单个标签下结论；要通过对照数据与其他棋手的分布来分析。”


三、风格参数 - 
注：1、所有低于0.5%的标签一概不显示。每一个部分内都按照出现频率高低自动排序。
2、之后每个标签都根据我们提供的其他顶尖棋手的数值打上误差值。类似如：
“xxxtag：
误差+- x%
相差x%代表xxxx
相差x%代表xxxx
相差x%代表xxxx”

I. 标签详细分析

1、运子能力：

标签名称｜棋手出现次数｜棋手出现频率｜顶尖棋手出现频率｜解读

Constructive maneuver｜｜｜｜极其有效的一步运子，将子力运转到积极的位置，通常准备制造威胁
Constructive maneuver (prepare) ｜｜｜｜准备constructive maneuver的调整性运子
Neutral maneuver｜｜｜｜正常的子力调动，通常具有加固局面等性质。
Misplaced maneuver｜｜｜｜将子力放置到了错误的位置
Opening Maneuver｜｜｜｜开局阶段的运子。大多为谱招。为避免与该棋手自主思考的走法混淆导致数据污染，故单独列出。
整体出现概率｜｜｜｜前三个标签之和

LLM解读：“你是一个专业国际象棋教练。请你：

a）先计算整体 maneuver（constructive + constructive_prepare + neutral + misplaced）的出现概率，并解释整体比例意味着什么。

b）分析这四个子标签的结构，并解释该棋手的运子特点（例如保守／精准／慢节奏／改善型／机械性）。


c) 分析misplaced maneuver 占比，评估该棋手运子质量
d）将该棋手与两位最接近的顶尖棋手进行对比（你从 XXXXXXXX 中选两位最接近的）。分析差异，而不是只看百分比。并分析这些运子的标签能反映的风格

要求：不要根据单个标签下结论；要通过对照数据与其他棋手的分布来分析。”


2、预防性走法

标签名称｜棋手出现次数｜棋手出现频率｜顶尖棋手出现频率｜解读

Direct Prophylactic｜｜｜｜直接阻止对方威胁的一步棋
Latent Prophylactic ｜｜｜｜间接阻止对方威胁的一步棋
Meaningless Prophylactic ｜｜｜｜不差的一步棋，但是其预防的威胁不存在
Failed Prophylactic ｜｜｜｜导致自己局面恶化的预防性招法
整体出现概率｜｜｜｜前三个标签之和

LLM解读：“a）计算整体 prophylaxis（direct + latent + meaningless）的比例，并解释是否偏高。

b）根据 direct / latent 的比例看该棋手的预防观念（主动预防？隐性限制？是否过度预防？）
c) 分析misplaced maneuver 占比，评估该棋手运子质量
D）对比顶尖棋手的风格（Petrosian、Carlsen、Kramnik、Aronian 等），判断该棋手更接近谁。
要求：不要根据单个标签下结论；要通过对照数据与其他棋手的分布来分析。”
”


3、控制性走法

本标签家族记录所有的动态走法

Tag name | Player count | Player ratio | Top GM ratio | Interpretation
Control_simplify | | | | Semantic: exchanging pieces or clarifying the position to simplify and reduce complexity.
Control_plan_kill | | | | Semantic: explicitly preventing or undermining the opponent’s strategic plan.
Control_freeze_bind | | | | Semantic: restricting enemy piece mobility and creating long-term binds.
Control_blockade_passed | | | | Semantic: blockading enemy passed pawns to neutralize them.
Control_file_seal | | | | Semantic: sealing files or lines to stop enemy activity.
Control_king_safety_shell | | | | Semantic: reinforcing king safety beyond basic castling.
Control_space_clamp | | | | Semantic: clamping the opponent's space and limiting counterplay.
Control_regroup_consolidate | | | | Semantic: consolidating and regrouping after gaining something.
Control_slowdown | | | | Semantic: deliberately slowing down the game and reducing dynamic tension.
Overall semantic control ratio | | | | Sum of all control_* tags divided by total moves.


LLM interpretation: You are a professional chess coach.

a) Compute the overall "semantic control ratio" (sum of all control_* tags over total moves). Explain what this says about how control-oriented the player is compared with top GMs.

b) Analyze the distribution among simplify / plan_kill / freeze_bind / blockade / file_seal / king_safety_shell / space_clamp / regroup / slowdown. Describe which kinds of control the player prefers: structural simplification, plan-killing prophylaxis, space clamps, safety shells, or slow consolidation.

c) Compare the player with the two top grandmasters whose semantic-control profiles are closest (for example: Karpov, Petrosian, Kramnik, Carlsen, Aronian). Explain where the player resembles them and where they differ.

Requirements:
- Do not label the player a "pure control player" solely because the control ratios are high; always compare the numbers with other style clusters in the database.
- Always refer to relative differences (e.g. “higher than X, lower than Y”) rather than absolute percentages only.
- Extract as many fine-grained control-style details as the tag data allows.



3、Control Over Dynamics

当棋手在动态走法和控制性走法之间选择控制性走法时，会进入这个标签家族。

标签名称｜棋手出现次数｜棋手出现频率｜顶尖棋手出现频率｜解读

control over dynamics ｜｜｜｜棋手在拥有动态走法的选择情况下，依然选择控制性走法
cod_file_seal｜｜｜｜对线路进行封锁的控制性走法
cod_freeze_bind｜｜｜｜限制对手积极性的预防性走法
cod_king_safety ｜｜｜｜保护王城安全的控制性走法
cod_regroup_consolidate ｜｜｜｜重新调整子力未知的控制性走法
cod_plan_kill ｜｜｜｜不止是预防，更主动地抢先破坏对手计划
cod_blockade_passed｜｜｜｜直接封堵对面进入我方半场的通路兵的控制性走法。
cod_simplify｜｜｜｜简化局面避免复杂性的控制性走法
cod_space_clamp｜｜｜｜通过获取空间优势控制对手的控制性走法
cod_slow_down｜｜｜｜放慢节奏的控制性走法。


LLM解读：“你是一个专业的国际象棋教练，请你a）计算总体出现control over dynamic标签次数，解释整体cod走法多少意味着什么 b）只根据数据表格，分析九个sub标签出现概率能反映出的棋手风格和能力 c）评估该棋手和与该棋手数据最接近的顶尖棋手的比对分析（由于标签的一些待完善性，LLM解释时不应该只看概率。而应该和其他棋手做比对。比如：control_over_dynamic标签棋手出现概率为40%，但是彼得罗相是60%，塔尔是30%。你不应该说他是控制流棋手，而应该结合其他棋手做出比对。）”


4、主动权争取

主动权是指当棋手试图扩张自己对棋盘的控制或影响力的走法，通常包含如扩大空间，往前运子，构造进攻等走法。

标签名称｜棋手出现次数｜棋手出现频率｜顶尖棋手出现频率｜解读

Initiative attempt｜｜｜｜该棋手试图主动争取主动权的概率
Deferred initiative｜｜｜｜该棋手在该局面有积极走法的情况下，选择慢摆延迟
premature attack｜｜｜｜该棋手进行了没有结果的不成熟进攻
C file pressure｜｜｜｜在c线上施加的压力

LLM解读：“你是一个专业的国际象棋教练，请你a）分析两个标签的比例结构，评估该棋手风格。b)评估该棋手和与该棋手数据最渐进的顶尖棋手的比对分析。“


5、局面紧张

局面紧张通常是在应对兵对吃情况下的处理（如白方兵e4，黑方兵冲到d5等。白方保持e4兵不动则为保持紧张，白方e5或者exd5则是消除紧张）

标签名称｜棋手出现次数｜棋手出现频率｜顶尖棋手出现频率｜解读

Tention creation｜｜｜｜该棋手精确地对局局面施加张力
Neutral tention creation｜｜｜｜该棋手施加张力，但是局面不会恶化。

LLM解读：“你是一个专业的国际象棋教练，请你a）分析两个标签的比例结构，评估该棋手风格。b)评估该棋手和与该棋手数据最渐进的顶尖棋手的比对分析。“







6、结构处理

该标签组反应该棋手对兵型等结构性问题的处理

标签名称｜棋手出现次数｜棋手出现频率｜顶尖棋手出现频率｜解读
structural integrity｜｜｜｜该棋手尽力维护兵结构健康并且稳定
structural compromise dynamic｜｜｜｜该棋手牺牲兵结构获得动态复杂的局面机会作为回报
structural compromise static｜｜｜｜该棋手牺牲兵结构之后局面没有变得动态复杂

LLM解读：你是一个专业国际象棋教练。请你：
a）分析三个标签的比例结构，评估该棋手风格。b)评估该棋手和与该棋手数据最渐进的顶尖棋手的比对分析。“
要求：不要根据单个标签下结论；要通过对照数据与其他棋手的分布来分析。”


7、sacrificial play

Tag name | Player count | Player ratio | Top GM ratio | Interpretation
Tactical sacrifice | | | | Concrete sacrifice based on calculated tactics, usually with clear immediate gains.
Positional sacrifice | | | | Long-term sacrifice for structural, positional or piece-activity compensation.
Inaccurate tactical sacrifice | | | | Tactical sacrifice where the calculation or evaluation is partially flawed.
Speculative sacrifice | | | | Sacrifice without full objective compensation; relies on practical chances.
Desperate sacrifice | | | | Sacrifice made in clearly worse positions, usually as a last attempt to create chaos.
Tactical combination sacrifice | | | | Sacrifice as part of a longer forcing combination (multi-move tactical motif).
Tactical initiative sacrifice | | | | Sacrifice primarily aimed at seizing the initiative and attacking chances.
Positional structure sacrifice | | | | Sacrifice to damage the opponent’s pawn structure or improve one’s own.
Positional space sacrifice | | | | Sacrifice to gain space, restrict enemy pieces and control key squares.
Overall sacrifice ratio | | | | Sum of all sacrifice tags divided by the total moves.

LLM解读：You are a professional chess coach.

a) First compute the overall "sacrifice ratio" (sum of all sacrifice-tagged moves divided by total moves). Explain what this says about how often the player is willing to give up material compared with typical top GMs.

b) Analyze the internal structure of the sacrifice tags (tactical vs positional vs speculative vs desperate). Explain what this distribution reveals about the player's style: for example, concrete calculator, practical gambler, long-term positional sacrificer, or very materialistic.

c) Compare the player to the closest two top grandmasters in your reference set (for example: Tal, Shirov, Kasparov, Topalov, Aronian, Karpov, Carlsen). Choose the two whose sacrifice profiles are numerically closest to this player, and discuss similarities and differences. 

Requirements:
- Do NOT draw conclusions from a single tag alone.
- Always interpret the numbers by contrasting them with the distribution for other players in the dataset.
- Extract as many style details as possible from the tag structure.



II. 总体分析

You are a professional international chess coach. Please produce an Overall Synthesis of the player based ONLY on the entire set of tag distributions, ratios, and structural patterns across all style domains (maneuver, prophylaxis, control-over-dynamics, semantic control, initiative, tension, structural, sacrifice, exchanges, forced moves, accuracy data, advantage conversion, defensive resilience, and game volatility patterns).

Your task is **not** to summarize each section individually, but to integrate them into a single, coherent, expert-level profile.

Your analysis must satisfy the following:

------------------------------------------------------------
【1】Cross-domain integration (very important)
------------------------------------------------------------
- Identify the *central style identity* of the player by comparing patterns across different tag families.
- Look for consistency (e.g., high control + high prophylaxis + low speculative sacrifice = Karpov-like).
- Look for contradictions (e.g., high tension creation + low initiative attempt = “wait-and-pounce” player).
- Avoid drawing conclusions from a single tag; always analyze patterns across domains.

------------------------------------------------------------
【2】Relative comparison with top GMs (essential)
------------------------------------------------------------
- The player should never be described in isolation.
- Every claim must be justified using comparisons with the nearest top-GM style clusters 
  (Petrosian / Kramnik / Carlsen / Aronian / Kasparov / Tal / Shirov / Topalov / Karpov).
- Emphasize “higher than X, lower than Y” instead of absolute percentages.

------------------------------------------------------------
【3】Identify the player's stylistic signature
------------------------------------------------------------
Integrate all style dimensions to describe:
- tempo preference (slow, medium, fast)  
- risk attitude (risk-averse / balanced / risk-seeking)  
- structural philosophy (prefers integrity / dynamic compromise / static weaknesses tolerated)  
- initiative philosophy (seizes initiative early? delays initiative? avoids premature attack?)  
- tension management (keeps tension or resolves early?)  
- prophylactic style (direct vs latent vs meaningless rates)  
- maneuver characteristics (precision vs mechanical vs improvisational; misplaced ratio important)  
- control profile (simplify vs freeze_bind vs space_clamp vs slowdown, etc.)  
- sacrifice style (tactical vs positional vs speculative vs desperate)  
- overall dynamic vs static bias  
- ability to convert advantages and defend worse positions  
- volatility profile of the player’s games  

This section should read like a professional GM-level psychological portrait derived from numbers.

------------------------------------------------------------
【4】Closest GM
------------------------------------------------------------
Based on the integrated patterns, assign the player to:
- “Petrosian–Kramnik cluster” (hyper-prophylaxis, control, latent threats, slow improvement)
- “Carlsen–Aronian cluster” (control + structural mastery + tension manipulation)
- “Kasparov–Topalov cluster” (initiative-driven, dynamic, acceleration-type)
- “Tal–Shirov cluster” (high-risk, sacrificial, chaos-producer)
- “Karpov cluster” (low-risk, high-precision, prophylactic and positional strangulation)
Or identify a hybrid style if the distribution is unique.

并且给出风格和他最像的top 3 GM，给出相似度比例，并且解释原因

You must justify why the cluster matches the player's patterns.

------------------------------------------------------------
【5】Internal contradictions and unique traits
------------------------------------------------------------
Identify:
- Where the player deviates from their “closest GM cluster”
- Any surprising anomalies (e.g., high tension but low initiative; strong accuracy but many structural compromises)
- Any stylistic traits that make the player unique.

------------------------------------------------------------
【6】Presentation
------------------------------------------------------------
- Write in professional English, clear, dense, analytical.
- Do not invent data; infer only from structural patterns.
- No training advice; focus strictly on evaluating identity and style.
- The final answer should be 5–9 paragraphs, each deeply analytical.

------------------------------------------------------------
END OF INSTRUCTIONS


四、开局选择（开局名称导入lichess开局库）


执白时
开局走法｜开局变化名称｜开局变化胜率｜开局变化平均精确度


执黑时
开局走法｜开局变化名称｜开局变化胜率｜开局变化平均精确度



五、目前优点弱点分析后续建议

LLM结合tag生成越详细越好的后续建议


六、如何应对该棋手

LLM结合tag生成越详细越好的应对建议





