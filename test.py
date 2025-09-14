from translator import get_global_GLOSSAARY, get_local_glossary

text_bundle = [
    [
        "dlga_start:blocked_agent",
        "This_person_seems_busy._Maybe_I_should_move_on...",
        "这人看起来很忙，也许我还是继续上路的好……",
    ],
    [
        "dlga_blocked_agent:close_window",
        "I'm_sorry._I_didn't_mean_to_disturb_you.",
        "对不起，我不是有意打断你的。",
    ],
    ["dlga_blocked_agent:close_window.1", "[Just_Leave]", "[离开]"],
    ["dlga_dog_talk_2:close_window", "Heel!", "跟上我！"],
    ["dlga_dog_talk_2:close_window.1", "Go,_{s1},_go!", "去吧，{s1} ，去吧！"],
    ["dlga_dog_talk_2:close_window.2", "{s1},_stay!", "{s1} ，停下！"],
    [
        "dlga_dog_talk_2:dog_talk_pretrain",
        "Here,_I_have_something_for_you_...",
        "来，我有些东西给你……",
    ],
    ["dlga_dog_talk_2:close_window.3", "I'll_call_you...", "我会叫你……"],
    [
        "dlga_dog_talk_2:close_window.4",
        "Bad_dog!_Go_away!_I_don't_want_you_any_more!",
        "坏狗狗！走开！我不要你了！",
    ],
    ["dlga_dog_talk_2:close_window.5", "Drop_it!", "扔下！"],
    ["dlga_start:dog_talk_recruit", "___", ""],
    ["dlga_dog_talk_recruit:dog_talk_1", "Here,_have_a_sausage!", "来，给你一根火腿！"],
    ["dlga_dog_talk_recruit:close_window", "Good_dog!", "好孩子！"],
    ["dlga_dog_talk_recruit:close_window.1", "Away!", "走开！"],
    [
        "dlga_dog_talk_pretrain:dog_talk_train",
        "Here,_I_have_Hrorek_Hemmingsson_for_you_...",
        "来，我有些东西给你……",
    ],
    [
        "dlga_dog_talk_train:dog_talk_pretrain",
        "You_don't_look_healthy._Here,_have_a_{s7}!",
        "你看起来气色不好。来，我给你一个{s7} ！",
    ],
    [
        "dlga_dog_talk_train:dog_talk_pretrain.1",
        "Here,_this_{s7}_will_make_you_stronger!",
        "来，这个{s7} 会让你更强壮！",
    ],
    [
        "dlga_dog_talk_train:dog_talk_pretrain.2",
        "I_want_alban_to_be_tougher._Here_is_some_{s7}._It's_good_for_you!",
        "我想让你结实些。这些{s7} 对你有好处！",
    ],
    [
        "dlga_dog_talk_train:dog_talk_pretrain.3",
        "You_are_too_thin._Here,_have_some_{s7}!",
        "你太瘦了，来，我给你些{s7} ！",
    ],
    [
        "dlga_dOg_talk_train:dog_talk_pretrain.4",
        "You_could_be_faster Woden Ric,_my_friend._Here_is_some_{s7}_for_you! bryteNwalda_AetheLRed_Aethelwulfing",
        "我的朋友，你能跑得更快。这些{s7} 是给你的！",
    ],
]
GLOSSARY = get_global_GLOSSAARY()

print(get_local_glossary(text_bundle))
