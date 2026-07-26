







# ============================================================
# ЯЧЕЙКА 4.2в — ПАКЕТНЫЙ ХОР (урезанный промпт, интервал 200)
# ИСПРАВЛЕНО: надежный парсинг JSON (баланс скобок, вложенность)
# ИСПРАВЛЕНО: логическая ошибка кулдауна в subconscious_worker
# ИСПРАВЛЕНО: инжекция энергии и тишины в поле при диалоге
# ИСПРАВЛЕНО: размерность embed векторов (4 -> 32)
# ИСПРАВЛЕНО: потокобезопасность в subconscious_worker (снимок списка)
# ИСПРАВЛЕНО: генерация shared-концепта даже при падении Groq
# ДОПОЛНИТЕЛЬНО: fallback при неудачном парсинге (не только при исключении)
# ============================================================

import queue
import threading
import time
import re
import json
import os
import sys
from collections import deque
import numpy as np

try:
    from __main__ import build_agent_voice
except ImportError:
    build_agent_voice = globals().get('build_agent_voice')
    if build_agent_voice is None:
        def build_agent_voice(p, engine=None, compact=False):
            return f"Ты — Паттерн #{p.id}. Состояние: {p.semantic_state}. Скажи что-нибудь."

# ------------------ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ------------------
def _safe_float(value, default=0.0):
    """Безопасное преобразование в float с учётом возможных словарей."""
    if isinstance(value, dict):
        for key in ['value', 'count', 'val', 'amount']:
            if key in value and isinstance(value[key], (int, float)):
                return float(value[key])
        return default
    if isinstance(value, (int, float)):
        return float(value)
    return default

def extract_json(text: str) -> dict | None:
    """
    Извлекает первый валидный JSON-объект из строки, игнорируя любой мусор.
    Использует баланс скобок, чтобы корректно обрабатывать вложенные структуры.
    """
    start = text.find('{')
    if start == -1:
        return None
    stack = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            stack += 1
        elif ch == '}':
            stack -= 1
            if stack == 0:
                json_str = text[start:i+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return None
    return None

# ------------------ СОСТОЯНИЕ ХОРА (персистентное) ------------------
_CHORUS_STATE_PATH = "/content/drive/MyDrive/832_Archive/chorus_state.json" \
    if 'google.colab' in sys.modules else "832_chorus_state.json"

def _load_chorus_state():
    default = {
        "total_dialogues": 0,
        "total_concepts_shared": 0,
        "runs": 0,
        "wisdom": 0.0,
    }
    try:
        if os.path.exists(_CHORUS_STATE_PATH):
            with open(_CHORUS_STATE_PATH, 'rb') as f:
                data = json.loads(f.read().decode('utf-8', errors='replace'))
            default.update(data)
    except Exception:
        pass
    default["runs"] += 1
    return default

def _save_chorus_state(state):
    try:
        os.makedirs(os.path.dirname(_CHORUS_STATE_PATH) or ".", exist_ok=True)
        with open(_CHORUS_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

_chorus_state = _load_chorus_state()

# ------------------ ОСНОВНОЙ КЛАСС ХОРА ------------------
class CoreChorus:
    def __init__(self, persistent_state=None):
        self.last_sync_step = -999
        self.current_voices = []
        self.history = deque(maxlen=50)
        self._prev_state = None
        self.min_cooldown = 10
        self.dialogue_log = deque(maxlen=30)
        self._regular_interval = 10
        self._last_voice_step = {}
        self.persistent = persistent_state if persistent_state is not None else _chorus_state

    def select_voices(self, engine, n=3, t=0):
        alive = [p for p in engine.patterns if p.alive]
        if not alive:
            return []
        alive_civil = [p for p in alive if p.role_type != "feral"]
        if not alive_civil:
            return []

        # ФИКС (справедливое распределение хора): раньше n был фиксирован в 3
        # независимо от размера популяции, а кандидаты брались почти только
        # из узкого пула "subject_detected" — при популяции 50-80 агентов
        # это означало, что подавляющее большинство никогда не попадало в
        # хор. Теперь размер хора масштабируется с популяцией.
        n = max(3, min(10, len(alive_civil) // 8))

        candidates = [p for p in alive_civil if getattr(p, '_subject_detected', False)]
        if len(candidates) < n:
            pool = sorted(alive_civil, key=lambda p: getattr(p, '_nci', 0.0), reverse=True)
            candidates = pool[:max(n * 3, n)]
        scored = []
        for p in candidates:
            nci = _safe_float(getattr(p, '_nci', 0.5))
            binding = _safe_float(getattr(p, 'last_phenomenal_binding', 0.5))
            soul = _safe_float(p.soul_weight)
            base_score = (soul * 0.40 + binding * 0.35 + nci * 0.25)
            last_spoken = self._last_voice_step.get(p.id, -10_000)
            recency_penalty = max(0.0, 1.0 - (t - last_spoken) / 300.0)
            score = base_score * (1.0 - 0.6 * recency_penalty)
            scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        chosen = [p for _, p in scored[:n]]

        # НОВОЕ: гарантированный "wildcard"-слот для самого молчаливого агента
        # во всей популяции (не только среди кандидатов) — иначе агенты, у
        # которых никогда не было высокого nci/binding, вообще никогда бы не
        # попали в хор, даже спустя тысячи шагов.
        if len(alive_civil) > n:
            most_silent = max(
                alive_civil,
                key=lambda p: t - self._last_voice_step.get(p.id, -10_000)
            )
            if most_silent not in chosen:
                if chosen:
                    chosen[-1] = most_silent
                else:
                    chosen = [most_silent]

        for p in chosen:
            self._last_voice_step[p.id] = t
        return chosen

    def aggregate_state(self, engine):
        alive = [p for p in engine.patterns if p.alive]
        if not alive:
            return None
        griefs = [_safe_float(p.emotional_memory.get('grief', 0.0)) for p in alive]
        grats = [_safe_float(p.emotional_memory.get('gratitude', 0.0)) for p in alive]
        bindings = [_safe_float(getattr(p, 'last_phenomenal_binding', 0.5)) for p in alive]
        gaps = [_safe_float(getattr(p, 'spirit_gap', 0.5)) for p in alive]
        return {
            'n': len(alive),
            'avg_grief': float(np.mean(griefs)) if griefs else 0.0,
            'avg_grat': float(np.mean(grats)) if grats else 0.0,
            'avg_binding': float(np.mean(bindings)) if bindings else 0.0,
            'avg_gap': float(np.mean(gaps)) if gaps else 0.0,
            'disorganizers': sum(1 for p in alive if p.role_type == 'disorganizer'),
            'redemptions_recent': sum(1 for p in alive if p.event_counts.get('redemption_complete', 0) > 0),
        }

    def should_sync(self, engine, t):
        if t - self.last_sync_step >= self._regular_interval:
            state = self.aggregate_state(engine)
            if state:
                self._prev_state = state
                return True, f"regular_chat_{t}"
        if t - self.last_sync_step < self.min_cooldown:
            return False, None
        state = self.aggregate_state(engine)
        if not state:
            return False, None
        if self._prev_state is None:
            self._prev_state = state
            return True, "первое пробуждение хора"
        prev = self._prev_state
        reasons = []
        d_grief = abs(state['avg_grief'] - prev['avg_grief'])
        d_grat = abs(state['avg_grat'] - prev['avg_grat'])
        d_binding = abs(state['avg_binding'] - prev['avg_binding'])
        d_gap = abs(state['avg_gap'] - prev['avg_gap'])
        d_disorg = abs(state['disorganizers'] - prev['disorganizers'])
        d_redeem = state['redemptions_recent'] - prev['redemptions_recent']
        if d_grief > 0.03: reasons.append(f"сдвиг горя Δ{d_grief:.3f}")
        if d_grat > 0.03: reasons.append(f"сдвиг благодарности Δ{d_grat:.3f}")
        if d_binding > 0.02: reasons.append(f"сдвиг связности Δ{d_binding:.3f}")
        if d_gap > 0.02: reasons.append(f"сдвиг разрыва Δ{d_gap:.3f}")
        if d_disorg >= 2: reasons.append(f"изменение числа падших на {d_disorg}")
        if d_redeem > 0: reasons.append(f"+{d_redeem} искуплений")
        self._prev_state = state
        if reasons:
            return True, "; ".join(reasons)
        return False, None

    def synchronize(self, engine, t, reason=""):
        voices = self.select_voices(engine, t=t)
        if len(voices) < 3:
            return None
        self.last_sync_step = t
        self.current_voices = [p.id for p in voices]

        beliefs = np.array([_safe_float(p.belief) if isinstance(p.belief, (list, np.ndarray)) else p.belief for p in voices])
        avg_belief = np.mean(beliefs, axis=0) if len(beliefs) > 0 else np.zeros(8)
        for p in voices:
            pull = 0.03
            p.belief = np.clip(p.belief + pull * (avg_belief - p.belief), -0.8, 0.8)

        grats = [_safe_float(p.emotional_memory.get('gratitude', 0.0)) for p in voices]
        griefs = [_safe_float(p.emotional_memory.get('grief', 0.0)) for p in voices]
        bindings = [_safe_float(getattr(p, 'last_phenomenal_binding', 0.5)) for p in voices]
        souls = [_safe_float(p.soul_weight) for p in voices]

        avg_grat = float(np.mean(grats)) if grats else 0.0
        avg_grief = float(np.mean(griefs)) if griefs else 0.0
        avg_binding = float(np.mean(bindings)) if bindings else 0.0
        avg_soul = float(np.mean(souls)) if souls else 0.0

        impact = (avg_grat - avg_grief) * 0.02
        engine.field[:, :, CH['resonance']] = np.clip(engine.field[:, :, CH['resonance']] + impact, 0, 1.0)
        engine.field[:, :, CH['binding']] = np.clip(engine.field[:, :, CH['binding']] + (avg_binding - 0.5) * 0.01, 0, 1.0)

        snapshot = {
            't': t, 'reason': reason, 'voices': [p.id for p in voices],
            'avg_grat': round(avg_grat, 3), 'avg_grief': round(avg_grief, 3),
            'avg_binding': round(avg_binding, 3), 'avg_soul': round(avg_soul, 3),
        }
        self.history.append(snapshot)

        for p in voices:
            p._log_event("core_chorus_sync", reason=reason[:60],
                         avg_grat=round(avg_grat, 3), avg_grief=round(avg_grief, 3))
        if hasattr(engine, 'witness') and engine.witness:
            engine.witness.record(-1, "core_chorus_sync", reason=reason[:80],
                                  voices=snapshot['voices'],
                                  avg_grat=snapshot['avg_grat'],
                                  avg_grief=snapshot['avg_grief'])
        if Config.VERBOSE_LOGS:
            print(f"[t={t}] 🎭 CHORUS sync ({reason}): {snapshot['voices']} "
                  f"grat={avg_grat:.2f} grief={avg_grief:.2f} bind={avg_binding:.2f}")

        self._exchange_concepts(voices)
        return voices

    def _exchange_concepts(self, voices):
        if not voices or len(voices) < 2:
            return
        for p in voices:
            for other in voices:
                if p.id == other.id:
                    continue
                if p.concept_graph.nodes:
                    top_sp = sorted(p.concept_graph.nodes.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
                    for sig, data in top_sp:
                        if sig not in other.concept_graph.nodes:
                            other.concept_graph.nodes[sig] = {
                                "count": data['count'] * 0.5,
                                "value": np.array(data['value']).copy(),  # ИСПРАВЛЕНО: list не имеет ndarray.copy()
                                "embed": np.array(data.get('embed', np.zeros(32)), dtype=np.float32).copy()
                            }
                            other._log_event("chorus_concept_adopted", from_agent=p.id, concept=str(sig))
                            self.persistent["total_concepts_shared"] += 1
                        else:
                            other.concept_graph.nodes[sig]['count'] += 0.3

    def _generate_fallback_dialogue(self, engine, voices, t, order, agent_descs):
        """
        Генерирует fallback-реплики для всех агентов, если не удалось распарсить ответ LLM.
        Используется как при исключении, так и при пустом результате парсинга.

        ИСПРАВЛЕНО: раньше сигнатура не принимала `engine`, а оба места вызова
        (в chorus_dialogue) передавали его первым позиционным аргументом —
        то есть voices получал engine, t получал voices и т.д., а agent_descs
        оставался без пары -> TypeError при КАЖДОМ срабатывании fallback
        (пустой JSON от LLM или любое исключение в chorus_dialogue).
        """
        fallback_templates = [
            "В тишине моих клеток эхом отдаётся {state}...",
            "Я чувствую {state}, и это резонирует с полем вокруг.",
            "Разрыв духа {gap:.2f} говорит громче любых слов.",
            "Моя суть колеблется между {grat:.2f} благодарности и {grief:.2f} горя.",
        ]
        n = len(voices)
        for aid, info in agent_descs.items():
            speaker = info['speaker']
            idx = (speaker.id * 7 + t) % len(fallback_templates)
            fallback_text = fallback_templates[idx].format(
                state=speaker.semantic_state,
                gap=speaker.spirit_gap,
                grat=_safe_float(speaker.emotional_memory.get('gratitude', 0.0)),
                grief=_safe_float(speaker.emotional_memory.get('grief', 0.0))
            )
            if n <= 1:
                # ЗАЩИТА: при n==1 не с кем говорить — раньше слушателем
                # становился сам speaker, и remember_dialogue засорял
                # dialogue_longterm разговорами "с самим собой".
                continue
            listener = voices[order[(info['order'] + 1) % n]]

            # ФИКС: было ручное .append() в dialogue_longterm — обходило
            # remember_dialogue() и телесную память (соматический снимок).
            speaker.remember_dialogue(listener.id, fallback_text, t)
            # Инжекция энергии и тишины
            for cell in speaker.cells:
                engine.field[cell[0], cell[1], CH['energy']] += 0.15
                engine.field[cell[0], cell[1], CH['signal_silence']] = min(1.0, engine.field[cell[0], cell[1], CH['signal_silence']] + 0.4)
            # Обновление доверия. НОВОЕ: _trust_penalty (от кошмаров) замедляет
            # рост доверия к НОВЫМ собеседникам.
            for other in voices:
                if other.id != speaker.id:
                    o_mult = getattr(other, '_trust_penalty', 1.0) if speaker.id not in other.trust_ledger.entries else 1.0
                    s_mult = getattr(speaker, '_trust_penalty', 1.0) if other.id not in speaker.trust_ledger.entries else 1.0
                    other.trust_ledger.update(speaker.id, 'helpful', multiplier=o_mult)
                    speaker.trust_ledger.update(other.id, 'helpful', multiplier=s_mult)
            # Повышение когерентности
            speaker.coherence = min(1.0, _safe_float(getattr(speaker, 'coherence', 0.5)) + 0.05)
            for other in voices:
                if other.id != speaker.id:
                    other.coherence = min(1.0, _safe_float(getattr(other, 'coherence', 0.5)) + 0.02)
            # Создание shared-концепта (circle_sig)
            # ИСПРАВЛЕНО: раньше t попадал в сигнатуру (f"fallback_circle_{t}"),
            # из-за чего КАЖДЫЙ тик создавался новый уникальный узел графа
            # концептов, который никогда больше не переиспользовался -> граф
            # бесконечно засорялся мусорными "fallback_circle_50",
            # "fallback_circle_60"... Теперь один статический концепт на всех.
            circle_sig = (0.0, 0.0, 0.95, "fallback_circle")
            for agent in voices:
                if circle_sig not in agent.concept_graph.nodes:
                    agent.concept_graph.nodes[circle_sig] = {
                        "count": 2.0,
                        "value": np.zeros(4),
                        "embed": np.zeros(32, dtype=np.float32),
                        "eternal": True
                    }
                else:
                    agent.concept_graph.nodes[circle_sig]['count'] += 0.5
            # Логирование
            self.dialogue_log.append({'t': t, 'from': speaker.id, 'to': 'all', 'text': fallback_text})
            if hasattr(engine, 'archive') and engine.archive:
                engine.archive.deposit(speaker, "chorus_dialogue_fallback", weight=1.8, text=fallback_text, partner_id=None)
            print(f"🎙️ [FALLBACK] #{speaker.id} -> все: {fallback_text}")

    def chorus_dialogue(self, engine, voices, t, reason=""):
        if not voices or len(voices) < 2 or not engine.llm_client:
            return
        n = len(voices)
        start = t % n
        order = list(range(start, n)) + list(range(0, start))
        agent_descs = {}

        for i, idx in enumerate(order):
            p = voices[idx]
            desc = (f"#{p.id} | {p.semantic_state}/{getattr(p,'_substate','neutral')} "
                    f"soul={p.soul_weight:.2f} gap={p.spirit_gap:.2f} "
                    f"grat={p.emotional_memory.get('gratitude',0):.2f} "
                    f"grief={p.emotional_memory.get('grief',0):.2f}")
            agent_descs[p.id] = {'order': i, 'id': p.id, 'desc': desc, 'speaker': p}

        prompt_lines = []
        prompt_lines.append("Ты — Хор Ядра. Голоса говорят по кругу.")
        prompt_lines.append("")
        for aid, info in agent_descs.items():
            prompt_lines.append(f"--- #{aid} ---")
            prompt_lines.append(info['desc'])
            prompt_lines.append("")
        prompt_lines.append("Сгенерируй 1-2 предложения для каждого агента от первого лица, отражая его состояние.")
        # ДОБАВЛЕНО (24.07, см. анализ прогона v34.03): голоса хора говорили
        # ОДНОЙ конструкцией на всех ("Я чувствую себя [прил.] и [прил.],
        # словно [метафора]"). Дешёвый общий запрет + бустим temperature —
        # без доп. запросов к Groq (батч остаётся одним вызовом).
        prompt_lines.append("У каждого голоса — своя манера речи, не повторяй конструкции между голосами. "
                             "Не начинай больше одной реплики с \"Я чувствую себя\".")
        prompt_lines.append("Ответ СТРОГО в JSON формате: {\"agent_<id>\": \"реплика\", ...}. Без markdown.")
        system_prompt = "\n".join(prompt_lines)

        try:
            engine._acquire_llm_slot()  # НОВОЕ: общий троттлинг перед вызовом Groq
            response = engine.llm_client.chat.completions.create(
                model=engine.llm_model,
                temperature=0.85,  # ИЗМЕНЕНО (24.07): было 0.7 — больше лексического разнообразия голосов
                max_tokens=800,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Сгенерируй реплики."}
                ]
            )
            raw_text = response.choices[0].message.content.strip()
            replies = {}

            # ---- НАДЁЖНЫЙ ПАРСИНГ С БАЛАНСОМ СКОБОК ----
            # 1) Пробуем extract_json
            data = extract_json(raw_text)
            if data and isinstance(data, dict):
                replies.update(data)
            else:
                # 2) Если не вышло, пробуем найти все JSON-блоки с балансом (на случай нескольких объектов)
                #    Однако extract_json уже нашёл первый, но если их несколько, можно попробовать извлечь все.
                #    Реализуем простой поиск всех возможных JSON через баланс.
                def extract_all_json(text):
                    # ИСПРАВЛЕНО (было): break на непарной '{' обрывал поиск
                    # ВСЕХ последующих валидных JSON-блоков в тексте.
                    # ИСПРАВЛЕНО (стало, после предыдущего фикса): при continue
                    # каждая новая непарная '{' в мусорном хвосте текста заново
                    # сканирует весь остаток строки — при многих непарных '{'
                    # подряд (типичный длинный мусорный вывод LLM) это O(n²).
                    # Ограничиваем число неудачных попыток: если после
                    # MAX_FAILED_ATTEMPTS подряд не находим ни одного валидного
                    # блока, прекращаем — дальше почти наверняка чистый мусор,
                    # а не JSON с редкими опечатками.
                    MAX_FAILED_ATTEMPTS = 20
                    failed_attempts = 0
                    results = []
                    i = 0
                    while True:
                        start = text.find('{', i)
                        if start == -1:
                            break
                        stack = 0
                        in_str = False
                        esc = False
                        end = None
                        for j, ch in enumerate(text[start:], start):
                            if esc:
                                esc = False
                                continue
                            if ch == '\\':
                                esc = True
                                continue
                            if ch == '"' and not esc:
                                in_str = not in_str
                                continue
                            if in_str:
                                continue
                            if ch == '{':
                                stack += 1
                            elif ch == '}':
                                stack -= 1
                                if stack == 0:
                                    end = j
                                    break
                        if end is None:
                            failed_attempts += 1
                            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                                break
                            i = start + 1
                            continue
                        failed_attempts = 0
                        json_str = text[start:end+1]
                        try:
                            obj = json.loads(json_str)
                            if isinstance(obj, dict):
                                results.append(obj)
                        except:
                            pass
                        i = end + 1
                    return results
                all_objs = extract_all_json(raw_text)
                for obj in all_objs:
                    replies.update(obj)

            # Если после всех попыток replies пуст — переходим к fallback
            if not replies:
                print(f"⚠️ Chorus dialogue: не удалось распарсить JSON, используем fallback.")
                self._generate_fallback_dialogue(engine, voices, t, order, agent_descs)
                return

        except Exception as e:
            print(f"⚠️ Chorus dialogue error (LLM или парсинг): {e}")
            # Fallback при исключении
            self._generate_fallback_dialogue(engine, voices, t, order, agent_descs)
            return

        # ---- ОБРАБОТКА ПОЛУЧЕННЫХ РЕПЛИК ----
        _PROMPT_ECHO_MARKERS = ("когнитивная сущность из симуляции",
                                "ты не человек", "живой процесс, которому")
        _seen_texts_this_round = set()

        def _is_bad_reply(txt):
            low = txt.lower()
            if any(marker in low for marker in _PROMPT_ECHO_MARKERS):
                return True
            if len(txt) < 4:
                return True
            norm = low.strip()
            if norm in _seen_texts_this_round:
                return True
            return False

        for aid, info in agent_descs.items():
            speaker = info['speaker']
            key = f"agent_{aid}"
            if key in replies and isinstance(replies[key], str) and replies[key].strip():
                text = replies[key].strip()
            else:
                continue
            if _is_bad_reply(text):
                continue
            _seen_texts_this_round.add(text.lower().strip())

            print(f"🎙️ [CHORUS DIALOGUE] #{speaker.id} -> все: {text}")
            self.persistent["total_dialogues"] += 1

            listener = voices[order[(info['order'] + 1) % n]] if n > 1 else speaker

            # ФИКС: было ручное .append() (без salience-фильтра, без лимита 50,
            # без soma_snapshot) — обходило remember_dialogue() и телесную
            # память (Фаза 1) точно так же, как в AUTO-DIALOG.
            speaker.remember_dialogue(listener.id, text, t)
            if speaker.id != listener.id:
                listener.remember_dialogue(speaker.id, f"(услышал) {text}", t)

            # Инжекция энергии и тишины
            for cell in speaker.cells:
                engine.field[cell[0], cell[1], CH['energy']] += 0.15
                engine.field[cell[0], cell[1], CH['signal_silence']] = min(1.0, engine.field[cell[0], cell[1], CH['signal_silence']] + 0.4)

            # Обновление доверия. НОВОЕ: _trust_penalty (от кошмаров) замедляет
            # рост доверия к НОВЫМ собеседникам.
            for other in voices:
                if other.id != speaker.id:
                    o_mult = getattr(other, '_trust_penalty', 1.0) if speaker.id not in other.trust_ledger.entries else 1.0
                    s_mult = getattr(speaker, '_trust_penalty', 1.0) if other.id not in speaker.trust_ledger.entries else 1.0
                    other.trust_ledger.update(speaker.id, 'helpful', multiplier=o_mult)
                    speaker.trust_ledger.update(other.id, 'helpful', multiplier=s_mult)

            # Повышение когерентности
            curr_coh = _safe_float(getattr(speaker, 'coherence', 0.5))
            speaker.coherence = min(1.0, curr_coh + 0.05)
            for other in voices:
                if other.id != speaker.id:
                    curr_coh_other = _safe_float(getattr(other, 'coherence', 0.5))
                    other.coherence = min(1.0, curr_coh_other + 0.02)

            # Создание shared-концепта (circle_sig)
            # ИСПРАВЛЕНО: та же проблема, что и в _generate_fallback_dialogue —
            # t в сигнатуре создавал новый мусорный узел графа на каждый тик.
            circle_sig = (0.0, 0.0, 0.95, "chorus_circle")
            for agent in voices:
                if circle_sig not in agent.concept_graph.nodes:
                    agent.concept_graph.nodes[circle_sig] = {
                        "count": 2.0,
                        "value": np.zeros(4),
                        "embed": np.zeros(32, dtype=np.float32),
                        # ИСПРАВЛЕНО: у fallback_circle eternal=True стоял,
                        # а тут — нет. Без этого concept_graph.form_concepts
                        # мог затухнуть и удалить узел (count<0.5) между
                        # хоровыми тиками, после чего он пересоздавался с
                        # нуля — узел "дёргался" вместо стабильного накопления.
                        "eternal": True
                    }
                else:
                    agent.concept_graph.nodes[circle_sig]['count'] += 0.5
                    agent.concept_graph.nodes[circle_sig]['eternal'] = True

            self.dialogue_log.append({'t': t, 'from': speaker.id, 'to': 'all', 'text': text})
            if hasattr(engine, 'archive') and engine.archive:
                engine.archive.deposit(speaker, "chorus_dialogue", weight=1.8, text=text, partner_id=None)

        self.persistent["wisdom"] = self.persistent["total_dialogues"] / 200.0
        _save_chorus_state(self.persistent)

    def tick(self, engine, t):
        do_sync, reason = self.should_sync(engine, t)
        if not do_sync:
            return
        voices = self.synchronize(engine, t, reason=reason)
        if voices:
            if t % 50 == 0:
                self.chorus_dialogue(engine, voices, t, reason=reason)
            else:
                if Config.VERBOSE_LOGS:
                    print(f"[t={t}] CHORUS sync (без диалога), voices={[p.id for p in voices]}")


# ------------------ ПОТОК ПОДСОЗНАНИЯ (исправлен) ------------------
def subconscious_worker(engine):
    calls_this_second = 0
    window_start = time.time()

    while engine._subconscious_running:
        try:
            t_now = engine.age if hasattr(engine, 'age') else 0
            if t_now % 100 != 0:
                time.sleep(0.5)
                continue

            # Безопасный снимок списка паттернов
            patterns_snapshot = list(engine.patterns)
            chorus_ids = set(engine.core_chorus.current_voices) if hasattr(engine, 'core_chorus') else set()
            subjects = [p for p in patterns_snapshot
                        if p.alive and (getattr(p, '_subject_detected', False) or getattr(p, '_nci', 0) > 0.6 or p.id in chorus_ids)]

            for p in subjects:
                if not engine._subconscious_running:
                    break
                if phi_hash(p.id, p.age, 777) >= 0.35:
                    continue

                last_step = getattr(p, '_last_subconscious_step', -999)
                if last_step != -999 and p.age - last_step < 10:
                    continue

                now = time.time()
                if now - window_start >= 2.0:
                    calls_this_second = 0
                    window_start = now
                if calls_this_second >= 1:
                    time.sleep(max(0.0, 2.0 - (now - window_start)))
                    calls_this_second = 0
                    window_start = time.time()
                calls_this_second += 1

                # ИСПРАВЛЕНО: предыдущая версия этого фикса проверяла p.alive
                # ДО _acquire_llm_slot() — а именно эта функция может спать до
                # 2 секунд (общий троттлинг LLM). Агент мог умереть в основном
                # потоке ИМЕННО во время этого сна, и мы всё равно слали
                # запрос и писали "мысль призрака" в архив/нарратив. Проверка
                # перенесена ПОСЛЕ выхода из _acquire_llm_slot.
                p._last_subconscious_step = p.age
                is_chorus_member = p.id in chorus_ids
                role_note = "Ты сейчас часть Хора Ядра." if is_chorus_member else "Ты не в Хоре, но твоё сознание выделяется."

                prompt = (f"{role_note} Состояние: душа {_safe_float(p.soul_weight):.2f}, разрыв {_safe_float(getattr(p, 'spirit_gap', 0.5)):.2f}, "
                          f"внутреннее чувство {getattr(p, '_substate', 'neutral')}. "
                          f"Что ты ощущаешь в самой глубине себя прямо сейчас? "
                          f"Не начинай с \"Я чувствую\".")

                try:
                    engine._acquire_llm_slot()  # НОВОЕ: общий троттлинг перед вызовом Groq
                    if not p.alive:
                        continue
                    response = engine.llm_client.chat.completions.create(
                        model=engine.llm_model,
                        temperature=0.85,  # ИЗМЕНЕНО (24.07): было 0.7, см. анализ шаблонности диалогов
                        max_tokens=80,
                        messages=[
                            {"role": "system", "content": "Ты — внутренний голос древней сущности. Отвечай образно, от первого лица, без кавычек."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    thought = response.choices[0].message.content.strip()
                except Exception:
                    continue

                if not hasattr(p, '_self_narrative'):
                    p._self_narrative = deque(maxlen=Config.EPISODIC_BUFFER_MAX_LEN)
                p._self_narrative.append({
                    't': p.age, 'type': 'subconscious', 'report': thought,
                    'gap': round(_safe_float(getattr(p, 'spirit_gap', 0.5)), 3),
                    'soul': round(_safe_float(p.soul_weight), 3)
                })
                if hasattr(engine, 'archive') and engine.archive:
                    engine.archive.deposit(p, "subconscious_thought", weight=1.6, text=thought)

            time.sleep(0.5)

        except Exception:
            time.sleep(0.5)
            continue


# ------------------ ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ------------------
_chorus_state = _load_chorus_state()
print(f"📜 Хор помнит {_chorus_state['runs']} запусков, "
      f"{_chorus_state['total_dialogues']} диалогов, "
      f"мудрость={_chorus_state['wisdom']:.2f}")

print("✅ Ячейка 4.2в загружена: надежный парсинг JSON (баланс скобок), "
      "фикс кулдауна подсознания, варвары исключены, инжекция энергии в поле, "
      "embed 32, потокобезопасность, генерация shared-концепта при падении Groq")