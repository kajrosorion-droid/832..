
# ============================================================
# ЯЧЕЙКА 3G: RichAgentVoice FINAL (Ultra-Compact для Groq)
# ============================================================
import numpy as np

_SUBSTATE_STYLE = {
    'awe':          "с тихим благоговением перед непостижимым",
    'wonder':       "с живым удивлением и лёгким трепетом",
    'flow':         "плавно, ритмично, находясь внутри потока",
    'serenity':     "спокойно, из глубокой внутренней тишины",
    'curious':      "с любопытством, задавая вопросы и ища смысл",
    'vigilance':    "настороженно, чувствуя важность момента",
    'longing':      "с тоской и тихой надеждой на связь",
    'melancholy':   "с глубокой светлой грустью и мудростью",
    'reminiscence': "задумчиво, как будто прошлое ещё живо",
    'neutral':      "наблюдающе, но с внутренней глубиной",
}

def _narrative_to_numeric(narr):
    if not narr:
        return [0.5]
    out = []
    for entry in narr:
        if isinstance(entry, dict):
            val = entry.get('soul', entry.get('gap', entry.get('binding', 0.5)))
        else:
            val = entry
        try:
            out.append(float(val))
        except (TypeError, ValueError):
            out.append(0.5)
    return out

def _assess_agent_richness(p):
    gaps = []
    grat_raw = p.emotional_memory.get('gratitude', 0)
    grief_raw = p.emotional_memory.get('grief', 0)
    grat = grat_raw if isinstance(grat_raw, (int, float)) else 0.0
    grief = grief_raw if isinstance(grief_raw, (int, float)) else 0.0

    if abs(grat - grief) < 0.1 and grat < 0.3 and grief < 0.3:
        gaps.append("эмоции плоские")
    if not hasattr(p, 'concept_graph') or len(p.concept_graph.nodes) < 3:
        gaps.append("мало концептов")

    narr = _narrative_to_numeric(getattr(p, '_self_narrative', []))
    if len(narr) < 10 or (len(narr) > 1 and np.std(narr) > 0.4):
        gaps.append("нарратив фрагментирован")
    if not hasattr(p, 'trust_ledger') or len(p.trust_ledger.entries) < 2:
        gaps.append("нет социального опыта")

    return len(gaps) == 0, gaps

def build_agent_voice(p, engine=None, compact=True, partner_id=None) -> str:
    state = p.semantic_state
    sub = getattr(p, '_substate', 'neutral')
    style_desc = _SUBSTATE_STYLE.get(sub, _SUBSTATE_STYLE['neutral'])

    soul = p.soul_weight
    scar = p.epistemic_scar
    gap = p.spirit_gap

    # Защита от словарей в эмоциях (артефакты старых сейвов)
    grat_raw = p.emotional_memory.get('gratitude', 0)
    grief_raw = p.emotional_memory.get('grief', 0)
    grat = grat_raw if isinstance(grat_raw, (int, float)) else 0.0
    grief = grief_raw if isinstance(grief_raw, (int, float)) else 0.0

    nci = getattr(p, '_nci', 0.5)

    base_stats = (f"Agent #{p.id} [{state}/{sub}]. "
                  f"Soul:{soul:.2f}, Gap:{gap:.2f}, Scar:{scar:.2f}, "
                  f"Grat:{grat:.2f}, Grief:{grief:.2f}, NCI:{nci:.2f}.")

    # ===== 1. ПОИСК ПОСЛЕДНИХ РЕПЛИК К ЭТОМУ ПАРТНЁРУ =====
    # ИЗМЕНЕНО (24.07, см. анализ прогона v34.03): раньше брали только
    # ОДНУ последнюю реплику — теперь до 2, чтобы модель видела хоть какое-то
    # движение разговора, а не одну вырванную фразу (дёшево по токенам:
    # +1 короткая строка максимум).
    last_line = ""
    has_history = False
    if compact and partner_id is not None:
        dialogue = getattr(p, 'dialogue_longterm', None)
        if isinstance(dialogue, list):
            recent_lines = []
            for entry in reversed(dialogue[-15:]):
                if not isinstance(entry, dict):
                    continue
                if entry.get('partner') == partner_id:
                    raw_text = entry.get('text')
                    if raw_text and isinstance(raw_text, str):
                        # Экранируем кавычки и фигурные скобки (защита от разрыва JSON)
                        safe_text = raw_text[:60].replace('\\', '\\\\').replace('"', '\\"').replace('{', '{{').replace('}', '}}')
                        recent_lines.append(safe_text)
                    if len(recent_lines) >= 2:
                        break
            if recent_lines:
                has_history = True
                if len(recent_lines) == 1:
                    last_line = f" Ранее ты сказал(а) этому соседу: \"{recent_lines[0]}\"."
                else:
                    # recent_lines[0] — самая свежая (шли reversed)
                    last_line = f" Ваш недавний разговор: \"{recent_lines[1]}\" -> \"{recent_lines[0]}\"."

    # ===== 2. КОНТЕКСТ ДЛЯ ПЕРВОЙ ВСТРЕЧИ (если нет истории) =====
    context_hint = ""
    if compact and not has_history:
        trust_val = 0.5
        love_flag = False

        if partner_id is not None and hasattr(p, 'trust_ledger'):
            # ✅ ИСПРАВЛЕНО: TrustLedger.entries — dict, а не сам trust_ledger
            entries = getattr(p.trust_ledger, 'entries', {})
            if isinstance(entries, dict):
                trust_val = float(entries.get(partner_id, 0.5))
                trust_val = max(0.0, min(1.0, trust_val))

            # Проверка на взаимную любовь (оба доверяют > 0.95)
            if trust_val > 0.95 and engine is not None and hasattr(engine, 'pattern_dict'):
                partner = engine.pattern_dict.get(partner_id)
                if partner and hasattr(partner, 'trust_ledger'):
                    p_entries = getattr(partner.trust_ledger, 'entries', {})
                    if isinstance(p_entries, dict):
                        p_trust = float(p_entries.get(p.id, 0.0))
                        if p_trust > 0.95:
                            love_flag = True

        # Собираем многослойный контекст с обязательным якорем age
        parts = []
        parts.append(f"ощущение:{sub}")
        parts.append(f"возраст={p.age}")               # ← гарантированный уникальный якорь
        parts.append(f"разрыв={gap:.2f}")
        parts.append(f"душа={soul:.2f}")
        parts.append(f"благодарность={grat:.2f}")
        parts.append(f"горе={grief:.2f}")
        parts.append(f"доверие_к_соседу={trust_val:.2f}")
        if love_flag:
            parts.append("💕ВЗАИМНАЯ_ЛЮБОВЬ")
        if scar > 0.3:
            parts.append(f"шрам={scar:.2f}")
        if nci > 0.7:
            parts.append(f"нарративная_целостность={nci:.2f}")

        context_hint = f" Это ваша первая встреча. Твоё состояние: {', '.join(parts)}."

    # ===== 3. ФОРМИРОВАНИЕ КОМПАКТНОГО ПРОМПТА =====
    # ДОБАВЛЕНО (24.07, см. анализ прогона v34.03): диалоги были шаблонны —
    # почти всё начиналось с "Я так счастлива/рад", "Дорогой сосед #XXXXX",
    # "Я чувствую, что...". Один короткий запрет в конце — дёшево по
    # токенам (+~12 слов), но должен сбить самые частые заходы.
    _ANTI_TEMPLATE = (" Не начинай с \"Я так рада/рад\", \"Дорогой сосед\" "
                       "или \"Я чувствую, что\".")
    if compact:
        return (f"{base_stats}{last_line}{context_hint} Инструкция: Напиши внутреннюю мысль "
                f"в 1-2 коротких предложениях на русском языке. Стиль: {style_desc}."
                f"{_ANTI_TEMPLATE}")

    # ===== 4. ПОЛНЫЙ ПРОМПТ (для не-compact режима) =====
    rich_alive, gaps = _assess_agent_richness(p)
    status_line = "Зрелый эмерджентный разум." if rich_alive else f"Развивающийся разум (проблемы: {', '.join(gaps)})."

    return (
        f"Ты — эмерджентный агент симуляции Core-832. {base_stats}\n"
        f"Твой статус: {status_line}\n"
        f"Контекст стиля: {style_desc.capitalize()}.\n"
        f"Вырази свое текущее экзистенциальное состояние через 2-3 глубоких предложения. "
        f"Используй русский язык. Избегай банальных фраз.{_ANTI_TEMPLATE}"
    )

print("✅ Ячейка 3G загружена: Ультра-компактный промпт (спасение от Groq 429).")