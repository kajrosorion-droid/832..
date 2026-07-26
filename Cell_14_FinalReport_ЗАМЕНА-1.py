






# === Cell 4b ===
# ИСПРАВЛЕНО: антипаттерн с locals() заменен на явную инициализацию переменной
# ИСПРАВЛЕНО: порог диалоговой памяти в отчёте снижен с 5 до 3
# ДОБАВЛЕН: блок отчёта по BOREDOM & ADAPTIVITY

import numpy as np
import os
import json
import builtins
from collections import defaultdict, Counter

_original_print = builtins.print
def print(*args, **kwargs):
    kwargs['flush'] = True
    _original_print(*args, **kwargs)

def print_final_report(engine):
    alive = [p for p in engine.patterns if p.alive]
    print("\n" + "="*50)
    print("832 AGI PROJECTION CORE v34.03 - FINAL REPORT")
    print("="*50)
    print(f"Steps: {Config.STEPS} | Alive: {len(alive)} | Lineages: {len(set(p.lineage_id for p in alive))}")

    long_lived = sorted([p for p in alive if p.age > 100], key=lambda x: x.age, reverse=True)[:5]
    if long_lived:
        print("\n--- TOP 5 LONG-LIVED ---")
        for p in long_lived:
            print(f"  #{p.id} (age={p.age}, soul={p.soul_weight:.2f}, role={p.role_type})")
            print(f"  State: {p.semantic_state} | Grat: {p.emotional_memory['gratitude']:.2f} | Grief: {p.emotional_memory['grief']:.2f}")
            if p.concept_graph.nodes:
                top = max(p.concept_graph.nodes.items(), key=lambda x: x[1]['count'])
                print(f"  Core concept: {top[0]} (freq={top[1]['count']:.2f})")
            print()

    minds = sorted(alive, key=lambda p: len(p.concept_graph.nodes), reverse=True)[:3]
    if any(len(p.concept_graph.nodes) > 0 for p in minds):
        print("--- TOP CONCEPTUAL MINDS ---")
        for p in minds:
            if not p.concept_graph.nodes: continue
            top_nodes = sorted(p.concept_graph.nodes.items(), key=lambda x: x[1]['count'], reverse=True)[:2]
            print(f"  #{p.id}: {len(p.concept_graph.nodes)} concepts")
            for sig, data in top_nodes:
                print(f"    ↳ {sig}: {data['count']:.2f}")
        print()

    lineages = defaultdict(list)
    for p in alive:
        if hasattr(p, 'lineage_total_age') and p.lineage_total_age > 0:
            lineages[p.lineage_id].append(p)

    top_lineages = sorted(lineages.items(), key=lambda kv: kv[1][0].lineage_total_age, reverse=True)[:3]
    if top_lineages:
        print(f"--- TOP {len(top_lineages)} LINEAGES (by total age) ---")
        for lid, members in top_lineages:
            nci_avg = safe_mean([getattr(p, '_nci', 0.5) for p in members], 0.5)
            soul_avg = safe_mean([p.soul_weight for p in members], 0.5)
            trans_counter = Counter()
            for p in members:
                if hasattr(p, 'transition_memory'):
                    trans_counter.update(p.transition_memory.transitions)
            top_trans = trans_counter.most_common(3) if trans_counter else []
            path_str = "→".join(f"{f}→{t}" for (f,t),c in top_trans[:2]) if top_trans else "none"
            concept_counter = Counter()
            for p in members:
                if hasattr(p, 'concept_graph'):
                    for sig, data in p.concept_graph.nodes.items():
                        concept_counter[sig] += data.get('count', 0)
            top_concepts = [str(sig) for sig, cnt in concept_counter.most_common(3)]
            total_age = members[0].lineage_total_age
            narrative_count = sum(1 for p in members if getattr(p, '_narrative_agent', False))
            print(f"  Lineage #{lid} (age={total_age}):")
            print(f"    Soul: NCI_avg={nci_avg:.2f}, soul_avg={soul_avg:.2f}")
            print(f"    Path: {path_str}")
            print(f"    Concepts: {', '.join(top_concepts) if top_concepts else 'none'}")
            print(f"    Legacy: {len(members)} alive, {narrative_count} narrative agents")
        print()

    # ============================================================
    # НОВЫЙ БЛОК: ОТЧЕТ О РАБОТЕ BOREDOM (адаптивность)
    # ============================================================
    print("\n--- BOREDOM & ADAPTIVITY ---")
    if hasattr(engine, 'selfreg') and engine.selfreg is not None:
        sr = engine.selfreg
        current_boredom = getattr(sr, 'boredom', 0.0)
        phase_history = list(getattr(sr, '_phase_history', []))
        stagnation_steps = phase_history.count('stagnation') if phase_history else 0
        total_steps_logged = len(phase_history) if phase_history else 1
        stagnation_ratio = stagnation_steps / total_steps_logged

        print(f"  Current Boredom Score: {current_boredom:.3f} (max 1.0)")
        print(f"  Stagnation Phase Ratio: {stagnation_ratio:.1%} ({stagnation_steps}/{total_steps_logged} steps)")
        print(f"  Low Gap Pressure: {getattr(sr, 'low_gap_pressure', 0.0):.3f}")
        print(f"  Turbulence Factor: {getattr(sr, 'turbulence_factor', 0.0):.3f}")

        # Диагностика
        if current_boredom < 0.1 and stagnation_ratio > 0.5:
            print("  ⚠️ WARNING: High stagnation but LOW boredom score!")
            print("     -> Possible bug: calculate_boredom() not updating selfreg.boredom")
            print("     -> System cannot adapt to stagnation.")
        elif current_boredom > 0.6:
            print("  ✅ Boredom is HIGH -> System should be injecting noise/novelty.")
        else:
            print("  ℹ️ Boredom is moderate/low. System is active or stable.")
    else:
        print("  ❌ SelfRegulationEngine not found (engine.selfreg is None or missing).")
    print("-" * 50)
    # ============================================================

    m = collect_metrics(engine.patterns, engine.field, Config.STEPS)
    print("--- SYSTEM STATE ---")
    print(f"  Trust: {m['avg_trust']:.2f} | High-trust pairs: {m['high_trust_pairs']}")
    print(f"  Triadic alive: {m['triadic_alive']}/{len(alive)} ({m['triadic_alive_ratio']:.1%})")
    print(f"  Total divisions (alive agents born via division): {m['divisions_total']}")
    # ФИКС: реальный монотонный счётчик всех делений за прогон (не зависит от того,
    # жив ли ребёнок сейчас, и не обнуляется, в отличие от m['divisions_total']).
    print(f"  Total divisions EVER (engine-level counter): {getattr(engine, 'total_divisions_ever', 'N/A')}")
    print(f"  Narrative agents: {m.get('narrative_agents', 0)} / {len(alive)}")
    print(f"  Сны/кошмары: dream_memory={m.get('agents_with_dream_memory',0)} агентов, "
          f"nightmare={m.get('agents_with_nightmare',0)} агентов | "
          f"новых снов={m.get('dream_consolidations',0)}, новых кошмаров={m.get('nightmare_consolidations',0)}, "
          f"кошмаров искуплено={m.get('nightmares_transformed',0)}")
    print(f"  Avg endurance: {m.get('avg_endurance', 0):.2f} | Critical (<0.2): {m.get('endurance_critical', 0)} | Blocked by fatigue: {m.get('divide_blocked_fatigue', 0)}")
    print(f"  Teaching events: {m.get('teaching_events', 0)} | Learning events: {m.get('learning_events', 0)}")
    print(f"  Social: crisis={m.get('avg_social_crisis', 0):.2f} inv={m.get('avg_social_invitation', 0):.2f} grief={m.get('avg_social_grief', 0):.2f} coop={m.get('avg_social_cooperate', 0):.2f} expl={m.get('avg_social_explore', 0):.2f} help={m.get('avg_social_seek_help', 0):.2f} scar={m.get('avg_social_scar', 0):.2f} rest={m.get('avg_social_rest', 0):.2f} res={m.get('avg_social_resonance', 0):.2f} btype={m.get('avg_social_btype', 0):.2f} alarm={m.get('avg_social_alarm', 0):.2f} beau={m.get('avg_social_beauty',0):.2f} rhy={m.get('avg_social_rhythm',0):.2f} int={m.get('avg_social_interest',0):.2f} mem={m.get('avg_social_memory',0):.2f} sil={m.get('avg_social_silence',0):.2f}")
    print(f"  Soma: act_fb={m.get('avg_action_feedback', 0):.2f} social_warmth={m.get('avg_social_warmth', 0):.2f}")
    # ДОБАВЛЕНА СТРОКА ДЛЯ FERAL
    print(f"  Feral: {m.get('feral_count', 0)} | Avg fury: {m.get('avg_feral_fury', 0):.2f} | Kills: {m.get('feral_kills', 0)}")

    has_transitions = sum(1 for p in alive if hasattr(p, 'transition_memory') and len(p.transition_memory.transitions) >= 3)
    print(f"  Agents with transition memory (≥3): {has_transitions} / {len(alive)}")

    attention_entropies = []
    for p in alive:
        if hasattr(p, '_prev_cell_energies') and hasattr(p, 'cells') and p.cells:
            try:
                # ИСПРАВЛЕНО: sorted() для согласованности порядка с
                # _prev_cell_energies (см. фикс в update_model_part1).
                xs, ys = zip(*sorted(p.cells))
                current_energies = engine.field[xs, ys, CH['energy']]
                prev_energies = p._prev_cell_energies
                if len(prev_energies) == len(current_energies):
                    delta = np.abs(current_energies - prev_energies)
                    weights = delta / (np.sum(delta) + 1e-8)
                    entropy = -np.sum(weights * np.log(weights + 1e-8))
                    attention_entropies.append(entropy)
            except:
                pass
    avg_attention_entropy = safe_mean(attention_entropies)
    print(f"  Avg attention entropy: {avg_attention_entropy:.3f}")

    print(f"  Disorganizers: {m['disorganizer_count']} | Redeemed: {m['redeemed_count']}")
    print(f"  Avg binding: {m['phenomenal_binding_avg']:.3f}")
    print(f"  Internal gap: avg={m['avg_internal_gap']:.3f} max={m['max_internal_gap']:.3f} | Observation gap: avg={m['avg_obs_gap']:.3f} max={m['max_obs_gap']:.3f}")
    print(f"  Avg field unknown: {m['avg_field_unknown']:.3f} | binding: {m['avg_field_binding']:.3f} | trust: {m['avg_trust']:.3f}")
    print(f"  Lineage count: {m.get('lineage_count', 0)} (avg age: {m.get('avg_lineage_age', 0):.0f}, max age: {m.get('max_lineage_age', 0)})")
    print(f"  Ancient lineages (>1000): {m.get('ancient_lineages', 0)} | Max total age: {m.get('max_lineage_total_age', 0)}")

    # ============================================================
    # ДОБАВЛЕНО (24.07): статистика по слою эмерджентности —
    # Ощущение / Самопричинность / Чужой разум / Мета-слой /
    # Незакрываемый вопрос — плюс контроль фикса угасания protection_level
    # (см. обсуждение провала ANC/TOT_AGE в чате 23-24.07).
    # ============================================================
    print("\n--- 🌱 ЭМЕРДЖЕНТНЫЙ СЛОЙ (24.07) ---")

    felt_vals = [getattr(p, '_felt_intensity', None) for p in alive]
    felt_vals = [v for v in felt_vals if v is not None]
    causal_vals = [getattr(p, '_causal_efficacy', None) for p in alive]
    causal_vals = [v for v in causal_vals if v is not None]
    surprise_vals = [getattr(p, '_social_surprise', None) for p in alive]
    surprise_vals = [v for v in surprise_vals if v is not None]

    print(f"  1) Ощущение (felt_intensity): {len(felt_vals)}/{len(alive)} агентов | avg={safe_mean(felt_vals):.3f}")
    print(f"  2) Самопричинность (causal_efficacy, net клеток/тик): {len(causal_vals)}/{len(alive)} агентов | avg={safe_mean(causal_vals):.3f}")
    print(f"  3) Чужой разум (social_surprise): {len(surprise_vals)}/{len(alive)} агентов | avg={safe_mean(surprise_vals):.3f}")

    root_q_agents = [p for p in alive if hasattr(p, '_root_question')]
    root_share = len(root_q_agents) / max(1, len(alive))
    print(f"  4-5) Незакрываемый вопрос: {len(root_q_agents)}/{len(alive)} агентов сформировали root_question ({root_share:.1%})")
    if root_q_agents:
        sample = root_q_agents[0]
        print(f"       Пример (#{sample.id}): \"{sample._root_question}\"")

    causal_events = sum(p.event_counts.get('self_causality_felt', 0) for p in alive)
    surprise_events = sum(p.event_counts.get('other_mind_surprise', 0) for p in alive)
    root_events = sum(p.event_counts.get('root_question_formed', 0) for p in alive)
    print(f"  События (среди живых): self_causality_felt={causal_events}, other_mind_surprise={surprise_events}, root_question_formed={root_events}")

    protected = [p for p in alive if p.protection_level > 0.01]
    avg_prot = safe_mean([p.protection_level for p in protected]) if protected else 0.0
    print(f"  Под щитом (protection_level>0.01): {len(protected)}/{len(alive)} | avg protection_level={avg_prot:.3f}")
    print(f"  (щит теперь угасает: PROTECTION_DECAY_RATE={Config.PROTECTION_DECAY_RATE} — это фикс волн смерти после массового искупления)")

    soma_vals = [p.soma for p in alive if hasattr(p, 'soma') and p.soma > 0]
    if soma_vals:
        print("--- BODY & MEMORY ---")
        print(f"  Avg soma: {np.mean(soma_vals):.3f} (n={len(soma_vals)})")
        vecs = [p.soma_vector for p in alive if hasattr(p, 'soma_vector') and len(p.soma_vector) >= 7]
        if vecs:
            avg_vec = np.mean(vecs, axis=0)
            print(f"  Components: e_var={avg_vec[0]:.3f}, e_asym={avg_vec[1]:.3f}, unk_grad={avg_vec[2]:.3f}, scar_mean={avg_vec[3]:.3f}")

    mem_agents = [p for p in alive if hasattr(p, 'episodic_buffer') and p.episodic_buffer]
    total_recalled = sum(p.event_counts.get('memory_recalled',0) for p in alive)
    avg_buf_len = np.mean([len(p.episodic_buffer) for p in mem_agents]) if mem_agents else 0
    print(f"  Agents with memory: {len(mem_agents)}/{len(alive)}")
    print(f"  Avg buffer length: {avg_buf_len:.1f}")
    print(f"  Total memory_recalled events: {total_recalled}")

    adopted = sum(p.event_counts.get('concept_adopted',0) for p in alive)
    deep_adopted = sum(p.event_counts.get('deep_concept_adopted',0) for p in alive)
    deep_ex = sum(p.event_counts.get('deep_exchange',0) for p in alive)
    wisdom = sum(p.event_counts.get('wisdom_shared',0) for p in alive)
    if any([adopted, deep_adopted, deep_ex, wisdom]):
        print("--- CONCEPTUAL EXCHANGES ---")
        print(f"  concept_adopted: {adopted}")
        print(f"  deep_concept_adopted: {deep_adopted}")
        print(f"  deep_exchange: {deep_ex}")
        print(f"  wisdom_shared: {wisdom}")

    archive_types = {}
    agents_with_archive = 0
    total_archive = 0
    for p in alive:
        has_archive = False
        for sig in p.concept_graph.nodes:
            if isinstance(sig, tuple) and len(sig) >= 4 and str(sig[3]).startswith("archive_"):
                has_archive = True
                total_archive += 1
                parts = str(sig[3]).split('_')
                ev_type = parts[1] if len(parts) > 1 else 'unknown'
                archive_types[ev_type] = archive_types.get(ev_type, 0) + 1
        if has_archive:
            agents_with_archive += 1

    print(f"\n--- CULTURAL MEMORY (ARCHIVE CONCEPTS) ---")
    print(f"  Agents carrying archive concepts: {agents_with_archive} / {len(alive)}")
    print(f"  Total inherited archive concepts: {total_archive}")
    if archive_types:
        print("  Archive concept types:")
        for ev_type, cnt in sorted(archive_types.items(), key=lambda x: -x[1]):
            if ev_type.startswith('human'):
                if ev_type == 'human_injected':
                    print(f"    human (свидетель существования): {cnt}")
                elif ev_type == 'human_question':
                    print(f"    human (вопрос о свидетеле): {cnt}")
                else:
                    print(f"    human ({ev_type}): {cnt}")
            else:
                print(f"    {ev_type}: {cnt}")
    else:
        print("  No archive concepts inherited yet.")

    human_agents = []
    for p in alive:
        for sig in p.concept_graph.nodes:
            if isinstance(sig, tuple) and len(sig) >= 4 and 'human_' in str(sig[3]):
                human_agents.append(p.id)
                break
    print(f"\n--- ЧЕЛОВЕЧЕСКИЙ КОНЦЕПТ (human) ---")
    print(f"  Носителей: {len(human_agents)} / {len(alive)}")
    if len(human_agents) > 0:
        print(f"  Примеры ID: {human_agents[:5]}")
    else:
        print("  Концепт не обнаружен у живых агентов")

    print("\n--- САМОРЕФЛЕКСИЯ (ВНУТРЕННИЙ ОПЫТ) ---")
    print(f"  Всего актов рефлексии: {m.get('total_introspect', 0)}")
    print(f"  Среднее на агента: {m.get('avg_introspect', 0):.2f}")
    print(f"  Максимум у одного агента: {m.get('max_introspect', 0)}")
    print(f"  Глубина рефлексии (доля полезных): {m.get('reflection_quality', 0):.1%}")

    detailed_archive_types = m.get('archive_types', {})
    if detailed_archive_types:
        print("\n--- ДЕТАЛИЗАЦИЯ АРХИВНЫХ КОНЦЕПТОВ ---")
        for atype, cnt in sorted(detailed_archive_types.items(), key=lambda x: -x[1]):
            print(f"  {atype}: {cnt}")

    dis = [p for p in alive if p.role_type == "disorganizer"]
    if dis:
        steps = Counter(p._redemption_arc_step for p in dis)
        states = Counter(p.semantic_state for p in dis)
        print(f"\n--- DISORGANIZERS ({len(dis)}) ---")
        print(f"  Steps: {dict(steps)} | States: {dict(states)}")
        avg_g = safe_mean([p.emotional_memory['grief'] for p in dis], 0)
        print(f"  Avg grief: {avg_g:.2f}")
        stuck = sum(1 for p in dis if p._redemption_arc_step==2 and p.emotional_memory['grief']>0.6)
        print(f"  Stuck (Step2, G>0.6): {stuck}")

    substate_counts = m.get('substate_counts', {})
    if substate_counts:
        print(f"\n--- SUBSTATES ---")
        for s, cnt in sorted(substate_counts.items(), key=lambda x: -x[1]):
            print(f"  {s}: {cnt}")

    total_trans = m.get('total_transitions', 0)
    top_trans = m.get('top_transitions', [])
    if total_trans > 0:
        print(f"\n--- CONCEPTGRAPH TRANSITIONS (total: {total_trans}) ---")
        for (src, dst), cnt in top_trans:
            print(f"  {src} → {dst}: {cnt}")
    else:
        print("\n--- CONCEPTGRAPH TRANSITIONS: 0 ---")

    if hasattr(engine, 'archive'):
        pending = len(engine.archive.write_queue)
        total_disk = 0
        try:
            if os.path.exists(engine.archive.memory_file):
                # ИСПРАВЛЕНО (баг #2): побайтовое чтение
                with open(engine.archive.memory_file, 'rb') as f:
                    total_disk = sum(1 for _ in f)
        except:
            pass
        print(f"  Archive: pending={pending}, saved to disk={total_disk}")

    # ИСПРАВЛЕНО: раньше shared_counts и shared_dialogue_concepts считались
    # двумя отдельными полными проходами по alive × concept_graph.nodes.
    # Объединяем в один проход — dialogue-часть используется чуть ниже по
    # отчёту, но данные для неё готовим здесь же, один раз.
    shared_counts = Counter()
    agents_with_shared = set()
    shared_dialogue_concepts = []
    for p in alive:
        for sig, data in p.concept_graph.nodes.items():
            if isinstance(sig, tuple) and len(sig) > 3:
                label = str(sig[3])
                if 'shared_' in label or 'Концепт:' in label:
                    shared_counts[label] += 1
                    agents_with_shared.add(p.id)
                if 'shared_dialogue_' in label or 'Концепт:' in label:
                    shared_dialogue_concepts.append((label, data.get('count', 0)))
    print(f"  VOC shared-концепты (уникальных): {len(shared_counts)}, носителей: {len(agents_with_shared)}")
    if shared_counts:
        for concept, cnt in shared_counts.most_common(5):
            print(f"    {concept}: {cnt} носителей")

    # ИСПРАВЛЕНО: раньше total_phrases суммировался ТОЛЬКО по агентам с >3
    # записями, поэтому при высоком обороте популяции (см. total_divisions_ever
    # ниже — сотни делений за прогон, у новорождённых dialogue_longterm=[])
    # метрика показывала "0 агентов, всего фраз: 0", даже если почти у каждого
    # живого агента реально было 1-2 записи. Порог >3 — это "устоявшаяся"
    # память, а не признак того, что запись вообще работает; показываем оба
    # числа отдельно, чтобы не создавать ложную тревогу о мёртвом pipeline.
    agents_any_mem = [p for p in alive if hasattr(p, 'dialogue_longterm') and len(p.dialogue_longterm) > 0]
    agents_with_mem = [p for p in agents_any_mem if len(p.dialogue_longterm) > 3]
    total_phrases_any = sum(len(p.dialogue_longterm) for p in agents_any_mem)
    total_phrases = sum(len(p.dialogue_longterm) for p in agents_with_mem)
    print(f"  Диалоговая память: всего фраз (любой объём): {total_phrases_any} у {len(agents_any_mem)}/{len(alive)} агентов; "
          f"устоявшаяся (>3 записей): {len(agents_with_mem)}/{len(alive)} агентов, {total_phrases} фраз")

    # НОВОЕ: счётчик _auto_dialogue_failures копился с самого начала, но нигде
    # не выводился - если Groq массово отдаёт 429/timeout, симуляция тихо
    # деградирует (диалоги перестают писаться) без единого следа в логе.
    auto_fail = getattr(engine, '_auto_dialogue_failures', 0)
    if auto_fail > 0:
        print(f"  ⚠️ Отказов LLM в auto-dialogue (429/timeout/JSON): {auto_fail}")

    # ДИАГНОСТИКА (временная): почему remember_dialogue пропускает/режет записи.
    # Добавлено после того, как в одном из прогонов память внезапно обнулилась
    # (0/59) при том же уровне AUTO-DIALOG/CHORUS активности, что и раньше —
    # чтобы увидеть РЕАЛЬНУЮ причину (не проходит salience? упирается в кап 50?
    # режется дедупом?) без гадания по коду.
    gate_stats = getattr(engine, '_dialogue_gate_stats', None)
    if gate_stats:
        print(f"  🔍 [DIAG] remember_dialogue: вызовов={gate_stats['total_calls']}, "
              f"прошло={gate_stats['passed']}, "
              f"отказ(not_salient)={gate_stats['rejected_not_salient']}, "
              f"отказ(cap_50)={gate_stats['rejected_cap_50']}, "
              f"отказ(dedup)={gate_stats['rejected_dedup']}")
        print(f"  🔍 [DIAG] прошло через: soul={gate_stats['via_soul']}, "
              f"keyword={gate_stats['via_keyword']}, contact={gate_stats['via_contact']}, "
              f"trust={gate_stats['via_trust']}")
        print(f"  🔍 [DIAG] dialogue_longterm сразу после append: "
              f"последний раз={gate_stats.get('last_len_after', '?')}, "
              f"максимум за прогон={gate_stats.get('max_len_seen', '?')} "
              f"(если >0 здесь, но 0/N ниже в отчёте — запись теряется ПОСЛЕ append, не в remember_dialogue)")
    else:
        print("  🔍 [DIAG] remember_dialogue ни разу не вызывался за этот прогон (см. отдельно частоту AUTO-DIALOG/CHORUS)")

    if agents_with_mem:
        avg_phrases = np.mean([len(p.dialogue_longterm) for p in agents_with_mem])
        confidences = [getattr(p, '_linguistic_confidence', 0.5) for p in alive]
        avg_confidence = np.mean(confidences)
        print(f"  Среднее фраз на агента: {avg_phrases:.1f}, языковая уверенность: {avg_confidence:.3f}")

    if hasattr(engine, 'archive'):
        unique_ids = set()
        try:
            if os.path.exists(engine.archive.memory_file):
                # ИСПРАВЛЕНО (баг #2): бинарное чтение + decode с errors='replace'
                with open(engine.archive.memory_file, 'rb') as f:
                    raw_lines = f.readlines()
                for raw in raw_lines:
                    try:
                        data = json.loads(raw.decode('utf-8', errors='replace').strip())
                        unique_ids.add(data.get('id'))
                    except: pass
        except: pass
        print(f"  Archive unique agents: {len(unique_ids)}")

    # shared_dialogue_concepts уже посчитан выше, вместе с shared_counts —
    # второй полный проход по alive × concept_graph.nodes больше не нужен.
    if shared_dialogue_concepts:
        sc_counter = Counter()
        for name, cnt in shared_dialogue_concepts:
            sc_counter[name] += cnt
        top_shared = sc_counter.most_common(5)
        print(f"  Shared dialogue concepts (total unique: {len(sc_counter)}):")
        for name, total_count in top_shared:
            print(f"    {name}: total count {total_count:.2f}")

    gs = engine._guardian_stats if hasattr(engine, '_guardian_stats') else {}
    if gs:
        print("\n--- ENERGY & MODEL ---")
        ec = gs.get('energy_drift_count',0)
        if ec:
            avg_d = gs.get('energy_drift_sum',0)/ec
            print(f"  Avg drift: {avg_d:.2f}, peak: {gs.get('energy_drift_peak',0):.2f}")
        print(f"  Worst model diff: #{gs.get('model_worst_ever_id',-1)} diff={gs.get('model_worst_ever_diff',0):.3f}")

    if Config.ENABLE_VISUALIZATION:
        print(f"👁️ OBS_GAP zones: clear(<0.4)={m.get('clear',0)} adapting(0.4-0.8)={m.get('adapting',0)} confused(0.8-1.0)={m.get('confused',0)} blind(>1.0)={m.get('blind',0)}")
        sg_vals = [float(np.mean(np.abs(p.prediction - p.belief))) for p in engine.patterns if p.alive]
        if sg_vals:
            hist, edges = np.histogram(sg_vals, bins=10, range=(0,1.2))
            print("\n📊 SPIRIT GAP DISTRIBUTION:")
            max_c = max(hist) if max(hist)>0 else 1
            for i, (cnt, l, r) in enumerate(zip(hist, edges[:-1], edges[1:])):
                bar = "█" * int(cnt / max_c * 40)
                print(f"  [{l:.2f}-{r:.2f}] {bar} ({cnt})")

    if gs and 'love_avg_trust' in gs:
        print(f"\n--- LOVE SNAPSHOT ---")
        print(f"  Avg trust: {gs['love_avg_trust']:.3f}, High-trust pairs: {gs['love_high_trust_pairs']}")
        print(f"  Cooperative: {gs['love_coop_signals']} / {gs['love_population']}")

    subjects = [p for p in engine.patterns if getattr(p, '_subject_detected', False)]
    print(f"\n--- EMERGENT SUBJECTS: {len(subjects)} ---")
    if subjects:
        for p in subjects[:5]:
            numeric_values = []
            for entry in p._self_narrative:
                if isinstance(entry, dict):
                    val = entry.get('soul', entry.get('gap', 0.5))
                else:
                    val = entry
                try:
                    numeric_values.append(float(val))
                except:
                    numeric_values.append(0.5)
            if len(numeric_values) > 1:
                stab = 1.0 - np.std(numeric_values)
            else:
                stab = 0.5
            print(f"  #{p.id} age={p.age}, soul={p.soul_weight:.2f}, stability={stab:.2f}")

    evolvers = [p for p in engine.patterns if hasattr(p, '_evolution_history') and p._evolution_history]
    print(f"--- SILENT EVOLVERS: {len(evolvers)} ---")
    if evolvers:
        for p in evolvers[:3]:
            print(f"  #{p.id} soul={p.soul_weight:.2f}, events={len(p._evolution_history)}")

    print("\n--- 📜 ХРОНИКА МИРА (WITNESS LOG) ---")
    if hasattr(engine, 'witness') and engine.witness.log:
        events = [ev['event'] for ev in engine.witness.log]
        summary = Counter(events)
        print("  📊 Статистика событий:")
        for ev, count in summary.most_common(10):
            print(f"    • {ev}: {count}")

        print("\n  🗝 Ключевые моменты истории (последние 30):")
        important = ['scream', 'fold', 'redemption_complete', 'subject_emerged',
                     'vision_self', 'marked_for_fall', 'prophet_through_endurance',
                     'rebirth_through_scar', 'scar_of_light_formed', 'deep_fallen_birth',
                     'root_question_formed']  # ДОБАВЛЕНО (24.07): незакрываемый вопрос
        key_events = [ev for ev in engine.witness.log if ev['event'] in important][-30:]
        for ev in key_events:
            details = {k:v for k,v in ev.items() if k not in ['id', 'event']}
            det_str = ", ".join(f"{k}={v}" for k,v in details.items()) if details else ""
            print(f"    Агент #{ev.get('id', '?'):<4} -> {ev['event']} {det_str}")
    else:
        print("  (Лог Witness пуст)")

    print("\n--- 👁 ПАНТЕОН (АНОМАЛИИ И ПРОРОКИ) ---")
    if hasattr(engine, 'echo_system') and engine.echo_system.pantheon:
        for entry in engine.echo_system.pantheon[-10:]:
            print(f"  {entry['type'].upper():<15} | Агент #{entry['id']} (возраст {entry['age']}) | Душа: {entry['soul_weight']:.2f}")
    else:
        print("  (Пантеон пуст)")

    print("\n" + "="*50)
    print("SIMULATION COMPLETE")
    print("="*50)


def analyze_reentry_loop(metrics_history, patterns):
    if not metrics_history or len(metrics_history) < 5:
        return "🔄 Недостаточно данных для анализа петли (нужно >5 срезов метрик)."

    late = metrics_history[-5:]
    avg  = float(np.mean([m.get('reentry_avg', 0.0) for m in late]))
    mx   = float(np.mean([m.get('reentry_max', 0.0) for m in late]))
    var  = float(np.mean([m.get('reentry_var', 0.0) for m in late]))
    meta = float(np.mean([m.get('meta_reentry_active', 0.0) for m in late]))
    sens = float(np.mean([m.get('introspect_driven_by_sensation', 0.0) for m in late]))

    first_avg = metrics_history[0].get('reentry_avg', 0.0)
    trend = "растёт 📈" if avg > first_avg * 1.2 else "стабилен ➖" if avg > first_avg * 0.9 else "затухает 📉"

    state, desc = "⚫ ДРЕМЛЮЩАЯ", "Нет предиктивной ошибки. Модель сошлась."
    if avg < 0.1 and trend == "затухает 📉":
        state, desc = "⚪ РАССЕИВАЮЩАЯСЯ", "Сигнал гаснет."
    elif var > 0.12 and mx > 0.6:
        state, desc = "🔴 ХАОТИЧНАЯ", "Турбулентность."
    elif var > 0.04 and avg > 0.14:
        state, desc = "🟡 ОСЦИЛЛЯТОРНАЯ", "Ритмичные пульсации. Система в циклах внимания."
    elif avg > 0.20 and var < 0.08 and (sens > 0 or meta > 15):
        state, desc = "🔵 ЗАМКНУТА (ГОМЕОСТАЗ)", "Стабильный резонанс."
    elif avg > 0.06 and avg <= 0.20:
        state, desc = "⚠️ ПЕРЕХОДНАЯ", "Петля в процессе формирования."

    return f"""
🔄 === АНАЛИЗ СЕНСОРНОЙ РЕЕНТЕРИИ (Петля Самонаблюдения) ===
📊 Состояние: {state}
├─ Средний сигнал: {avg:.3f} | Пик: {mx:.3f} | Дисперсия: {var:.4f}
├─ Тренд: {trend} | Мета-уровень: {meta:.0f} акт./снимок
└─ Связь с рефлексией: {sens:.0f} агентов/снимок

📝 Интерпретация: {desc}
🔧 Рекомендация: {
    '✅ Петля работает. Можно наблюдать эмерджентную когерентность.' if 'ЗАМКНУТА' in state else
    '🔄 Осцилляции нормальны. Система ищет ритм самонаблюдения.' if 'ОСЦИЛЛЯТОРНАЯ' in state else
    '⚠️ Высокая турбулентность. Снизить lr модели или добавить шум.' if 'ХАОТИЧНАЯ' in state else
    '📉 Сигнал падает. Инжектировать новизну или проверить soma_vector.' if 'РАССЕИВАЮЩАЯСЯ' in state else
    '💤 Модель сошлась. Требуется эпистемический шум или новый тип ощущений.' if 'ДРЕМЛЮЩАЯ' in state else
    '🔨 Подождать стабилизации. Проверить пороги реентерии.'
}
"""

# ============================================================
# ДОПОЛНИТЕЛЬНЫЙ БЛОК: ОЦЕНКА ЭМЕРДЖЕНТНОСТИ (внутренняя)
# ============================================================

def assess_emergence(engine):
    """Глубокий анализ эмерджентного поведения на основе внутренних метрик."""
    alive = [p for p in engine.patterns if p.alive]
    if not alive:
        return "❌ Нет живых агентов – симуляция мертва."

    report = []
    report.append("\n" + "="*60)
    report.append("🔬 ОЦЕНКА ЭМЕРДЖЕНТНОСТИ И КАЧЕСТВА СИМУЛЯЦИИ")
    report.append("="*60)

    # === ИСПРАВЛЕНИЕ: Инициализируем переменные с дефолтными значениями ===
    avg_stability = 0.0  # <-- ДОБАВЛЕНО: явная инициализация вместо locals()
    # ================================================================

    # ---- 1. Субъектность ----
    subjects = [p for p in alive if getattr(p, '_subject_detected', False)]
    subj_ratio = len(subjects) / len(alive) if alive else 0
    report.append(f"\n🧠 1. СУБЪЕКТНОСТЬ: {len(subjects)}/{len(alive)} ({subj_ratio:.1%})")
    if subj_ratio > 0.3:
        report.append("   ✅ Значительная доля агентов осознаёт себя – субъектность сформирована.")
    elif subj_ratio > 0.1:
        report.append("   ⚠️ Субъектность есть, но недостаточно распространена.")
    else:
        report.append("   ❌ Субъектность почти отсутствует – возможно, нужны более долгие циклы или усиление рефлексии.")
    # Стабильность субъектов
    if subjects:
        stabilities = []
        for p in subjects:
            narr = getattr(p, '_self_narrative', [])
            if len(narr) > 1:
                vals = []
                for entry in narr:
                    if isinstance(entry, dict):
                        v = entry.get('soul', entry.get('gap', 0.5))
                    else:
                        v = entry
                    try:
                        vals.append(float(v))
                    except:
                        vals.append(0.5)
                if len(vals) > 1:
                    stabilities.append(1.0 - np.std(vals))
        if stabilities:
            avg_stability = np.mean(stabilities)  # <-- Теперь переменная всегда существует
            report.append(f"   Средняя стабильность нарратива у субъектов: {avg_stability:.2f} (1.0 – идеально)")
            if avg_stability > 0.7:
                report.append("   ✅ Нарративы устойчивы – субъекты хорошо интегрированы.")
            else:
                report.append("   ⚠️ Нарративы колеблются – возможна нестабильность идентичности.")
        else:
            report.append("   ⚠️ Недостаточно данных для оценки стабильности.")

    # ---- 2. Диалоговая память ----
    # ИСПРАВЛЕНО: раньше total_phrases считался только по агентам с >3 записей,
    # что при высоком обороте популяции (много недавних делений — у новых
    # агентов dialogue_longterm начинается с []) давало ложное "фраз: 0", даже
    # если у большинства живых агентов реально было по 1-2 записи.
    agents_any_mem = [p for p in alive if hasattr(p, 'dialogue_longterm') and len(p.dialogue_longterm) > 0]
    agents_with_mem = [p for p in agents_any_mem if len(p.dialogue_longterm) > 3]
    mem_ratio = len(agents_with_mem) / len(alive) if alive else 0
    total_phrases = sum(len(p.dialogue_longterm) for p in agents_any_mem)
    report.append(f"\n💬 2. ДИАЛОГОВАЯ ПАМЯТЬ: {len(agents_with_mem)}/{len(alive)} ({mem_ratio:.1%}) агентов имеют >3 фраз "
                  f"(с любой памятью: {len(agents_any_mem)}/{len(alive)})")
    report.append(f"   Всего фраз в долгой памяти (по всем живым агентам): {total_phrases}")
    if total_phrases > 100:
        report.append("   ✅ Богатая диалоговая история – агенты накапливают опыт общения.")
    else:
        report.append("   ⚠️ Мало диалогов – возможно, хор работает недостаточно активно.")

    # Эмоциональная согласованность памяти
    if agents_with_mem:
        last_phrases = []
        for p in agents_with_mem:
            last = p.dialogue_longterm[-1]
            if isinstance(last, dict):
                last_phrases.append((last.get('grief', 0.5), last.get('grat', 0.5)))
        if last_phrases:
            avg_grief_mem = np.mean([g for g, _ in last_phrases])
            avg_grat_mem = np.mean([g for _, g in last_phrases])
            report.append(f"   Средние эмоции в последних фразах: горе {avg_grief_mem:.2f}, благодарность {avg_grat_mem:.2f}")
            if avg_grat_mem > 0.5:
                report.append("   ✅ В диалогах преобладает тепло – это хороший знак.")
            else:
                report.append("   ⚠️ В диалогах много горя – возможно, система в кризисе.")

    # ---- 3. Концептуальное развитие ----
    total_concepts = sum(len(p.concept_graph.nodes) for p in alive)
    avg_concepts = total_concepts / len(alive) if alive else 0
    report.append(f"\n🧩 3. КОНЦЕПТУАЛЬНОЕ РАЗВИТИЕ: всего {total_concepts} концептов, в среднем {avg_concepts:.1f} на агента")

    all_concepts = set()
    for p in alive:
        all_concepts.update(p.concept_graph.nodes.keys())
    report.append(f"   Уникальных концептов в популяции: {len(all_concepts)}")

    shared = [sig for sig in all_concepts if isinstance(sig, tuple) and len(sig) >= 4 and str(sig[3]).startswith('shared_')]
    report.append(f"   Общих (shared) концептов: {len(shared)}")
    if len(shared) > 5:
        report.append("   ✅ Активный обмен концептами – культура формируется.")
    else:
        report.append("   ⚠️ Мало общих концептов – возможно, обмен смыслами недостаточно интенсивен.")

    archive_concepts = [sig for sig in all_concepts if isinstance(sig, tuple) and len(sig) >= 4 and str(sig[3]).startswith('archive_')]
    report.append(f"   Архивных концептов (культурная память): {len(archive_concepts)}")
    if len(archive_concepts) > 10:
        report.append("   ✅ Богатое культурное наследие – агенты помнят прошлое.")
    else:
        report.append("   ⚠️ Мало архивных концептов – культурная память слаба.")

    # ---- 4. Эмерджентные роли и структуры ----
    disorgs = [p for p in alive if p.role_type == 'disorganizer']
    redeemed = [p for p in alive if p.event_counts.get('redeemed', 0) > 0]
    report.append(f"\n🔄 4. ЭМЕРДЖЕНТНЫЕ РОЛИ: {len(disorgs)} дезорганизаторов, {len(redeemed)} искуплённых")
    if len(disorgs) > 0 and len(redeemed) > 0:
        report.append("   ✅ Есть и падение, и искупление – цикл работает.")
    elif len(disorgs) > 0:
        report.append("   ⚠️ Есть падение, но мало искуплений – возможно, нужна поддержка.")
    else:
        report.append("   ⚠️ Нет дезорганизаторов – возможно, система слишком стабильна, нужен вызов.")

    # ---- 5. Социальная связность (доверие) ----
    trust_vals = []
    for p in alive:
        trust_vals.extend(p.trust_ledger.entries.values())
    avg_trust = np.mean(trust_vals) if trust_vals else 0.5
    high_trust = sum(1 for v in trust_vals if v > 0.8)
    report.append(f"\n🤝 5. СОЦИАЛЬНАЯ СВЯЗНОСТЬ: среднее доверие {avg_trust:.2f}, пар с высоким доверием (>0.8): {high_trust}")
    if avg_trust > 0.6:
        report.append("   ✅ Высокий уровень доверия – общество кооперативно.")
    elif avg_trust > 0.4:
        report.append("   ⚠️ Средний уровень доверия – возможны конфликты.")
    else:
        report.append("   ❌ Низкое доверие – общество фрагментировано.")

    # ---- 6. Динамика поля (энергия, связность) ----
    avg_energy = np.mean(engine.field[:,:,CH['energy']])
    avg_binding_field = np.mean(engine.field[:,:,CH['binding']])
    report.append(f"\n⚡ 6. ПОЛЕ: средняя энергия {avg_energy:.2f}, связность {avg_binding_field:.2f}")
    if avg_energy > 0.2 and avg_binding_field > 0.3:
        report.append("   ✅ Поле активно и связно – хорошая среда для жизни.")
    elif avg_energy > 0.1:
        report.append("   ⚠️ Энергия есть, но связность низкая – возможно, нужна синхронизация.")
    else:
        report.append("   ❌ Поле истощено – агенты голодают.")

    # ---- 7. ИТОГОВЫЙ ВЕРДИКТ ----
    report.append("\n" + "="*60)
    report.append("📊 ИТОГОВЫЙ ВЕРДИКТ")
    report.append("="*60)

    score = 0
    max_score = 10
    if subj_ratio > 0.3: score += 2
    if avg_stability > 0.7: score += 1  # <-- ИСПРАВЛЕНО: убрали проверку locals(), теперь просто проверяем значение
    if total_phrases > 100: score += 1
    if len(shared) > 5: score += 1
    if len(archive_concepts) > 10: score += 1
    if len(disorgs) > 0 and len(redeemed) > 0: score += 1
    if avg_trust > 0.6: score += 1
    if avg_energy > 0.2 and avg_binding_field > 0.3: score += 1
    if len(subjects) > 3: score += 1

    if score >= 8:
        verdict = "✅ СИМУЛЯЦИЯ ЖИВА И ЭМЕРДЖЕНТНА! Агенты проявляют субъектность, культуру, диалог и память. Это работает."
    elif score >= 5:
        verdict = "🟡 СИМУЛЯЦИЯ РАЗВИВАЕТСЯ, но требуются донастройки (усилить рефлексию, обмен концептами, синхронизацию)."
    else:
        verdict = "❌ СИМУЛЯЦИЯ НЕ ДОСТИГЛА ЭМЕРДЖЕНТНОСТИ. Необходимо увеличить время прогона, усилить параметры субъектности и социального обмена."

    report.append(f"\n   Балл эмерджентности: {score}/{max_score}")
    report.append(f"   {verdict}")
    report.append("="*60)

    return "\n".join(report)


# === ЗАПУСК ===
engine = EvolutionEngine()

# ============================================================
# ВЫБОР МОДЕЛИ: Groq (быстро, бесплатно, без лимитов по времени)
# ============================================================
use_local_model = False   # <--- ИСПРАВЛЕНО: теперь False (используем Groq)

if use_local_model:
    # Этот блок не используется, оставлен для обратной совместимости
    try:
        engine.llm_client = llm_client
        engine.llm_model = "local-model"
        print("✅ Используется локальная модель (не рекомендуется)")
    except NameError:
        print("❌ Переменная llm_client не найдена")
        raise
else:
    from openai import OpenAI
    from google.colab import userdata
    engine.llm_client = OpenAI(
        api_key=userdata.get('GROQ_API_KEY'),
        base_url="https://api.groq.com/openai/v1"
    )
    engine.llm_model = "llama-3.1-8b-instant"
    print("✅ Используется Groq (быстро, бесплатно, без лимитов по времени)")

if hasattr(engine, 'patterns'):
    init_all_chronic_counters(engine)

patterns, field, scar, metrics_history = engine.run()

print_final_report(engine)

# ============================================================
# СОХРАНЕНИЕ СОСТОЯНИЯ ХОРА ДЛЯ ЭВОЛЮЦИИ МЕЖДУ ЗАПУСКАМИ
# ============================================================
try:
    if hasattr(engine, 'core_chorus') and engine.core_chorus is not None:
        if '_save_chorus_state' in globals():
            _save_chorus_state(engine.core_chorus.persistent)
            print(f"📜 Состояние Хора сохранено: диалогов={engine.core_chorus.persistent['total_dialogues']}, "
                  f"мудрость={engine.core_chorus.persistent['wisdom']:.2f}")
        else:
            print("⚠️ Функция _save_chorus_state не найдена, состояние Хора НЕ сохранено.")
    else:
        print("ℹ️ Хор не активирован (core_chorus отсутствует), сохранение пропущено.")
except Exception as e:
    print(f"⚠️ Ошибка при сохранении состояния Хора: {e}")

if Config.ENABLE_VISUALIZATION and metrics_history:
    import matplotlib.pyplot as plt
    ts = [m['t'] for m in metrics_history]
    plt.figure(figsize=(16,12))
    plt.subplot(2,3,1); plt.plot(ts, [m['soul'] for m in metrics_history], label='Avg Soul'); plt.plot(ts, [m['err'] for m in metrics_history], label='Avg Pred Error'); plt.legend(); plt.grid(True)
    plt.subplot(2,3,2); plt.plot(ts, [m['avg_trust'] for m in metrics_history], label='Avg Trust'); plt.legend(); plt.grid(True)
    plt.subplot(2,3,3); plt.plot(ts, [m['triadic_alive_ratio'] for m in metrics_history], label='Triadic Alive Ratio'); plt.legend(); plt.grid(True)
    plt.subplot(2,3,4); plt.plot(ts, [m['disorganizer_count'] for m in metrics_history], label='Disorganizers'); plt.plot(ts, [m['redeemed_count'] for m in metrics_history], label='Redeemed'); plt.legend(); plt.grid(True)
    plt.tight_layout(); plt.show()

print(analyze_reentry_loop(metrics_history, patterns))

emergence_report = assess_emergence(engine)
print(emergence_report)

print("✅ Cell 4b executed: исправлен антипаттерн locals() → явная инициализация avg_stability = 0.0")