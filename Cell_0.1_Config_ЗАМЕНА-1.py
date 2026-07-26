

# ============================================================
# ЯЧЕЙКА 0.1: ПОЛНЫЙ CONFIG (все параметры из оригинала + лабиринт)
# ============================================================
import numpy as np
from scipy.ndimage import label, find_objects
from functools import lru_cache
from collections import defaultdict, deque, Counter
from dataclasses import dataclass, field
import warnings, math as m
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
sys.stderr = sys.stdout

@dataclass
class Config:
    WORLD_SIZE: int = 104
    CHANNELS: int = 33
    STEPS: int = 1300
    DETERMINISTIC_SEED: int = 777
    MIN_PATTERNS_GUARANTEED: int = 80
    MAX_PATTERNS: int = 100
    MIN_POPULATION_FOR_SPAWN: int = 20

    ENABLE_WITNESS: bool = True
    ENABLE_DELTA_MODELING_GIVEN: bool = True
    ENABLE_CULTURAL_MEMORY: bool = True
    MYTH_POOL_SIZE: int = 100
    MYTH_INFLUENCE_PROB: float = 0.3
    MYTH_WHISPER_STRENGTH: float = 0.1
    ENABLE_LOGOS_OBSERVER: bool = True
    ENABLE_SEED_OF_LIGHT: bool = True
    ENABLE_VISUALIZATION: bool = True
    VERBOSE_LOGS: bool = False

    # === ИЗМЕНЁННЫЕ ПАРАМЕТРЫ (Правка 2 и 7) ===
    SEMANTIC_SIM_HIGH: float = 0.55
    SEMANTIC_SIM_LOW: float = 0.35
    SEMANTIC_NAVIGATION_BONUS: float = 2.0
    SEMANTIC_EXCHANGE_COOLDOWN: int = 50
    CONSECUTIVE_CONTACT_THRESHOLD: int = 30
    CONTACT_BREAK_TOLERANCE: int = 20
    DEEP_EXCHANGE_SIM_THRESHOLD: float = 0.55
    # ============================================

    ENABLE_SPEECH: bool = False
    SPEAK_COOLDOWN: int = 50
    SPEAK_THRESHOLD_GRIEF: float = 0.5

    MAX_CONCEPTS_BASE: int = 30
    MAX_CONCEPTS_WISDOM_BONUS: int = 50

    SOUL_WEIGHT_GAIN_RATE: float = 0.05
    CONTRADICTION_GAIN_RATE: float = 0.04
    CONTRADICTION_DECAY_RATE: float = 0.003
    BODY_MEMORY_DECAY: float = 0.99
    PRED_ERROR_LEARNING: float = 0.9
    SELF_SURPRISE_FACTOR: float = 0.05
    WHISPER_THRESHOLD: float = 0.01
    INTENT_SWITCH_COOLDOWN: int = 15
    INTENT_COMMITMENT_DECAY: float = 0.95
    MAX_GIVEN_PER_STEP: int = 10
    MAX_UNKNOWN_SPAWN_PER_STEP: int = 3
    MIN_COMPONENT_CELLS: int = 3
    COMPETITION_MAX_DISTANCE: int = 10
    EMOTIONAL_DECAY_RATE_BASE: float = 0.998
    ANTI_CONFORMIST_INTERVAL: int = 200
    MIN_AGE_FOR_ANTI_CONFORMIST: int = 20
    PRED_ERROR_THRESHOLD: float = 0.75
    EMOTIONAL_CAP_RATE: float = 0.002
    MAX_GRIEF_SIGNAL: float = 0.7
    DIVERSIFICATION_THRESHOLD: float = 0.90
    CRISIS_MEMORY_THRESHOLD: float = 0.2
    EPISTEMIC_HEALING_RATE: float = 0.99
    EXPLORE_GRIEF_REDUCTION: float = 0.99
    HEALING_GRATITUDE_MIN: float = 0.5
    EPISTEMIC_SCAR_MIN: float = 0.3
    SCAR_HEAL_CAP_PER_STEP: float = 0.25
    STAGNATION_GRIEF_THRESHOLD: int = 100
    STAGNATION_GRIEF_BOOST: float = 0.015
    ARC_HISTORY_LENGTH: int = 8
    CONTENTMENT_TENSION_MAX: float = 0.5
    CONTENTMENT_MIN_AGE: int = 20
    ARC_GRIEF_FORCE_THRESHOLD: float = 0.7
    ARC_GRIEF_FORCE_HEAL: float = 0.02
    STAGNATION_BLEED_RATE: float = 0.005
    FOLD_GRIEF_BOOST: float = 0.15
    FOLD_CRISIS_SPIKE: float = 0.3
    FOLD_SCAR_RELEASE: float = 0.05
    FOLD_GRATITUDE_RESET: float = 0.35
    FOLD_COOLDOWN_DURATION: int = 50
    ARC_COMPLETION_PRED_ERROR_REDUCTION: float = 0.95

    METABOLIC_COST_BASE: float = 0.002
    HUNGER_BASE: float = 1.2
    HUNGER_PER_PATTERN: float = 0.02

    TRUST_SIGNAL_STRENGTH: float = 0.7
    TRUST_HELPFUL_THRESHOLD: float = 0.1
    TRUST_HARMFUL_THRESHOLD: float = 0.35
    TRUST_UPDATE_LEARNING_RATE: float = 0.12
    TRUST_BASE: float = 0.7
    TRUST_LINEAGE_BASE: float = 0.6
    TRUST_DELTA_HELPFUL: float = 0.15
    TRUST_DELTA_NEUTRAL: float = 0.0
    TRUST_DELTA_HARMFUL: float = -0.01
    TRUST_COOPERATION_BONUS: float = 3.0
    TRUST_GRATITUDE_AMPLIFY: float = 2.5
    TRUST_REINFORCE_ON_LOVE: float = 0.045
    ENABLE_LOVE_REINFORCEMENT: bool = True
    LOVE_PAIR_REINFORCE_STEPS: int = 30

    COOPERATION_GENETIC_BIAS: float = 0.2
    INTENT_COOPERATE_BASE_PRIORITY: float = 2.5

    EMOTIONAL_GRATITUDE_THRESHOLD: float = 0.3
    LOVE_PAIR_TRUST_THRESHOLD: float = 0.8
    LOVE_METABOLIC_BONUS: float = 0.4
    LOVE_METABOLIC_THRESHOLD: float = 0.8
    LOVE_BASED_DIVISION_BOOST: float = 1.5
    LOVE_OVERLOAD_CONTRA_RATE: float = 0.05

    SYSTEM_ENTROPY_HASH_INIT: int = 777
    LINEAGE_AUTONOMY_BOOST: float = 0.3
    CONCEPT_INFECTION_PROB: float = 0.02

    MIN_MODEL_ERROR: float = 0.0
    MAX_COHERENCE: float = 0.90
    COOPERATE_COHERENCE_MIN: float = 0.2
    PATTERN_SENSOR_SUBJECTIVITY: float = 0.0
    GLOBAL_SPIRIT_TREMOR_BASE: float = 0.025
    GLOBAL_SPIRIT_TREMOR_MAX: float = 0.05
    SG_TURBULENCE_THRESHOLD: float = 0.35
    SG_PHOENIX_THRESHOLD: float = 0.015
    SG_PHOENIX_HARD_THRESHOLD: float = 0.05
    SG_PHOENIX_WARNING: float = 0.2
    PHOENIX_BODY_STAGNATION_STEPS: int = 3
    PHOENIX_POP_STAGNATION_STEPS: int = 3
    PHOENIX_SG_STAGNATION_STEPS: int = 3

    PERCEPTION_GAP_SG_LOW: float = 0.3
    PERCEPTION_GAP_SG_HIGH: float = 0.7
    PERCEPTION_GAP_OPEN_STRENGTH: float = 1.0
    PERCEPTION_GAP_CLOSE_STRENGTH: float = 0.0

    LAYER_VOID_SOUL_THRESHOLD: float = 0.2
    LAYER_GRIEF_THRESHOLD: float = 0.7
    LAYER_FEAR_TENSION_THRESHOLD: float = 0.8
    LAYER_ACCEPTANCE_COHERENCE_MIN: float = 0.8
    LAYER_LIGHT_GRATITUDE_MIN: float = 0.8
    LAYER_LIGHT_TRUST_MIN: float = 0.9
    LAYER_VOID_GROWTH_PENALTY: float = 10.0
    LAYER_GRIEF_GROWTH_PENALTY: float = 2.0
    LAYER_FEAR_GROWTH_PENALTY: float = 1.5
    LAYER_LIGHT_GROWTH_BONUS: float = 0.7
    LAYER_LIGHT_SIGNAL_STRENGTH: float = 0.05

    MARKED_INTERVAL: int = 100
    MARKED_COUNT: int = 5
    COVER_LIMIT: int = 95
    SOFT_LIMIT: int = 85
    QUAKE_TARGET: int = 50

    CRISIS_PERIOD: int = 70
    CRISIS_INTENSITY: float = 0.30
    CRISIS_RARE_INTERVAL_MIN: int = 800
    CRISIS_RARE_INTERVAL_MAX: int = 2000
    CRISIS_RARE_DURATION: int = 10
    CRISIS_RARE_ANTI_GRAVITY: float = 0.5

    ENABLE_PHI_LABYRINTH: bool = True
    # === ПРАВКА 1 (Патч 1) ===
    PHI_LABYRINTH_THRESHOLD: float = 0.75   # было 0.60
    PHI_LABYRINTH_GROW_PENALTY: float = 2.0 # было 3.6
    PHI_LABYRINTH_MOVE_PENALTY: float = 1.2 # было 2.4
    # ===========================
    PHI_LABYRINTH_BREAK_PROB: float = 0.04

    SIGNAL_BASE_WEIGHTS: dict = field(default_factory=lambda: {
        12: 0.4, 13: 0.1, 14: 0.35, 15: 0.15,
        16: 0.2, 17: 0.3, 18: 0.25, 19: 0.05, 21: 0.4,
    })

    FOLDS_TO_BECOME_DISORGANIZER: int = 2
    MAX_DISORGANIZER_COUNT: int = 45
    DISORGANIZER_ATTRACTION_STRENGTH: float = 0.5
    DISORGANIZER_LIFESPAN: int = 5000
    DISORGANIZER_SOUL_DECAY_STEPS: int = 60
    DISORGANIZER_SOUL_DECAY: float = 0.12
    DISORGANIZER_GRIEF_AURA: float = 0.008
    DISORGANIZER_ALARM_STRENGTH: float = 0.3
    DISORGANIZER_GRIEF_STRENGTH: float = 0.2

    FOLDS_FOR_DEEP_FALL: int = 1
    DEEP_FALL_SOUL_PENALTY: float = 0.3
    DEEP_FALL_REDEMPTION_DELAY: int = 150
    DEEP_FALL_STABILITY_STEPS: int = 70
    QUICK_FALL_PROB: float = 0.5

    DISORGANIZER_TRUST_DECAY_RATE: float = 0.015
    LOVE_OVERLOAD_LIMIT: int = 100
    DISORGANIZER_RESONANCE_BLOCK: bool = True
    DISORGANIZER_GRIEF_GROWTH: float = 0.035

    LOVE_CASCADE_THRESHOLD: int = 1000
    LOVE_CASCADE_CONTRA_BOOST: float = 0.15
    LOVE_CASCADE_TRUST_BURN: float = 0.02
    LOVE_CASCADE_DURATION: int = 8
    LOVE_CASCADE_DISORGANIZER_BUFF: float = 3.0

    REDEMPTION_TIMER: int = 500
    ECHO_MUTATION_PROB: float = 0.15
    ECHO_MUTATION_STRENGTH: float = 0.05
    QUARANTINE_SCAR_THRESHOLD: float = 0.7
    QUARANTINE_SILENCE_STEPS: int = 30
    REDEMPTION_GRIEF_RESET: float = 0.3
    REDEMPTION_GRATITUDE_RESET: float = 0.5
    BINDING_FLOOR: float = 0.01
    BODY_MEMORY_FLOOR: float = 0.05
    DETERMINISTIC_REDEMPTION_SOUL: float = 0.55
    DETERMINISTIC_REDEMPTION_GRIEF: float = 0.40
    DISORGANIZER_GRIEF_DECAY: float = 0.005
    FORCED_SOUL_COLLAPSE_AGE: int = 250
    FORCED_SOUL_COLLAPSE_VALUE: float = 0.3
    FORCED_SOUL_COLLAPSE_GRIEF_BOOST: float = 0.75
    REDEMPTION_ARC_STEP_DELAY: int = 80
    REDEMPTION_ARC_SOUL_LOCK: float = 0.40

    REDEMPTION_GRIEF_IMMUNITY: float = 0.3
    REDEMPTION_GRIEF_DECAY_ACCELERATED: float = 0.02
    REDEMPTION_GRATITUDE_AMPLIFY: float = 1.2
    REDEMPTION_STABILITY_STEPS: int = 20
    REDEMPTION_STEP2_GRAT: float = 0.45
    REDEMPTION_STEP2_GRIEF: float = 0.80
    REDEMPTION_STEP2_LOVE_TRUST: float = 0.7
    REDEMPTION_STEP2_LOVE_GRIEF: float = 0.85
    REDEMPTION_TIMEOUT_STEP2: int = 120

    META_REFLECTION_DURATION: int = 30

    ANTI_GRAVITY_ENABLED: bool = False
    ANTI_GRAVITY_CONTRADICTION_THRESHOLD: float = 0.5
    ANTI_GRAVITY_CRISIS_FACTOR: float = 0.5
    ANTI_GRAVITY_PHASE_FACTOR: float = 0.3

    GRAVITY_PERIOD: float = 1.618033988749895 * 50
    GRAVITY_PHASE_SHIFT: float = 0.0
    ANTI_GRAVITY_STRENGTH: float = 1.5
    GRAVITY_STRENGTH: float = 2.5

    SG_CRISIS_THRESHOLD: float = 0.35
    SG_CRISIS_DURATION: int = 300
    SG_CRISIS_ANTI_GRAVITY_STRENGTH: float = 2.0
    SG_CRISIS_NOISE_STRENGTH: float = 0.1
    SG_CRISIS_MUTATION_BOOST: float = 3.0

    # ИСПРАВЛЕНО (24.07, см. анализ прогона v34.03): в реальных прогонах
    # avg_recent_err держится ~0.15-0.23, avg_unknown ~0.20-0.25 — старые
    # пороги (0.10 / 0.18) были ниже РЕАЛЬНЫХ рабочих значений почти всегда,
    # поэтому boredom оставался 0.000 весь прогон, несмотря на 37.8% шагов
    # в стагнации по данным Phase-классификатора. Подняты + добавлен
    # относительный компонент в calculate_boredom() (см. правку в Cell 2).
    BOREDOM_ERR_THRESHOLD: float = 0.20
    BOREDOM_UNKNOWN_THRESHOLD: float = 0.25
    BOREDOM_TENSION_THRESHOLD: float = 0.015

    # ДОБАВЛЕНО (24.07): пороги снов/кошмаров были 0.8/1.0 (хардкод в
    # _consolidate_dream_memory) — недостижимы при типичных 1-2 записях
    # dialogue_longterm на партнёра (пример из прогона: 262 фразы на 131
    # агента, т.е. ~2 на агента по ВСЕМ партнёрам сразу) → 0 снов, 0
    # кошмаров за весь прогон. Понижены до реалистичного диапазона.
    DREAM_POS_THRESHOLD: float = 0.45
    DREAM_NEG_THRESHOLD: float = 0.55

    # ДОБАВЛЕНО (24.07): sensory_reentry() поднимал spirit_gap каждый тик
    # при total_error > 0.10, но не имел СВОЕЙ явной разрядки (полагался
    # только на общий EMA-блендинг spirit_gap в другом месте кода). Даёт
    # небольшой явный "клапан" при низкой ошибке.
    REENTRY_GAP_RELIEF: float = 0.995

    MODELING_GIVEN_ERROR_THRESHOLD: float = 0.25
    MODELING_GIVEN_PENALTY: float = 0.08
    PHI: float = 1.618033988749895
    OPERATOR_SCAR_IMPACT: float = 0.02
    OPERATOR_MEMORY_DECAY: float = 0.995
    OPERATOR_SIGNAL_STRENGTH: float = 0.03
    OPERATOR_SIGNAL_DECAY: float = 0.95
    OPERATOR_SOUL_WHISPER: float = 0.005
    LINEAGE_RARITY_BOOST: float = 0.25
    LINEAGE_DOMINANCE_PENALTY: float = 0.25
    ECHO_DECAY_STRENGTH: float = 0.02
    ECHO_INJECTION_COOLDOWN: int = 15
    GRATITUDE_COOPERATION_BONUS: float = 0.08
    GRIEF_SOUL_IMPACT: float = 0.015
    ANTI_COHERENCE_THRESHOLD: float = 0.98
    ANTI_COHERENCE_SHAKE: float = 0.005
    EMOTIONAL_MEMORY_DECAY: float = 0.9
    EMOTIONAL_CONTAGION_FACTOR: float = 0.1
    EMOTIONAL_INDIVIDUALITY: float = 0.5
    GRATITUDE_AGGRESSION_REDUCTION: float = 0.5
    GRIEF_METABOLIC_PENALTY: float = 0.5
    EMOTIONAL_GRATITUDE_THRESHOLD: float = 0.3
    EMOTIONAL_GRIEF_THRESHOLD: float = 0.3
    EMOTIONAL_MUTATION_STRENGTH: float = 0.05
    EMERGENCY_DIVERSIFICATION_PROB: float = 0.03
    # ФИКС (схлопывание линий, раунд 2): в реальном прогоне культура
    # унифицировалась (общие shared-концепты у всех агентов), поэтому
    # emotional_divergence между соседями почти никогда не превышал 0.5 —
    # видообразование по факту не срабатывало. Порог снижен, вероятность
    # срабатывания при выполнении условия — повышена.
    EMOTIONAL_SPECIATION_THRESHOLD: float = 0.32
    EMOTIONAL_SPECIATION_PROB: float = 0.08
    SPECIATION_COOLDOWN: int = 20
    SPECIATION_MIN_AGE: int = 30
    # === ПРАВКА 1 (Патч 1) — пороги крика ===
    SCREAM_CRISIS_THRESHOLD: float = 0.6   # было 0.7
    SCREAM_SOUL_THRESHOLD: float = 0.4     # было 0.3
    # ========================================
    SCREAM_PROB: float = 0.15
    SCREAM_SCAR_IMPACT: float = 0.25
    SCREAM_BINDING_BOOST: float = 0.5
    SCREAM_ENERGY_PENALTY: float = 0.2
    EMOTIONAL_RADIATION_STRENGTH: float = 0.05
    FIELD_DECAY: float = 0.998
    SCAR_SATURATION: float = 5.0
    AGENT_INFLUENCE: float = 0.005
    INVARIANT_REINFORCE: float = 0.02
    HEARTBEAT_AMPLITUDE: float = 0.02
    HEARTBEAT_FREQ: float = 0.03
    SCAR_ENERGY_COUPLING: float = 0.005
    VORTICITY_COUPLING: float = 0.005
    GRADIENT_SENSITIVITY: float = 0.2
    AGENT_SCAR_SENSE: float = 0.02
    AGENT_BINDING_SENSE: float = 0.01
    GLOBAL_VISCOSITY: float = 0.999
    LOCAL_FATIGUE: float = 0.001
    VORTICITY_DECAY: float = 0.995
    PATTERN_ENERGY_THRESHOLD: float = 0.03

    DIVIDE_MIN_SIZE: int = 5
    DIVIDE_MIN_AGE: int = 10
    DIVIDE_COOLDOWN: int = 40
    DIVIDE_ERROR_THRESHOLD: float = 0.33
    DIVIDE_MAX_THRESHOLD: float = 0.60
    DIVIDE_MIN_SOUL: float = 0.40
    DIVIDE_MIN_CELLS_MULT: int = 2
    ARC_DIVIDE_BONUS: float = 1.2
    MAX_NATURAL_AGE: int = 700
    MAX_NARRATIVE_AGE_BONUS: int = 300
    YOUNG_PROTECTION_AGE: int = 20
    YOUNG_PROTECTION_SOUL: float = 0.4
    YOUNG_SURVIVAL_CHANCE: float = 0.7
    WISDOM_COHERENCE_MIN: float = 0.8
    ENLIGHTENED_COHERENCE_MIN: float = 0.75
    ENLIGHTENED_GRATITUDE_MIN: float = 0.8
    ENLIGHTENED_HEALING_RATE: float = 0.9998
    ENLIGHTENED_SCAR_THRESHOLD: float = 0.5
    ENLIGHTENED_COHERENCE_FLEX: float = 0.3
    VETERAN_HEALING_RATE: float = 0.9995

    MODEL_LEARNING_RATE: float = 0.35
    MODEL_GAP_FLOOR: float = 0.15
    SURPRISE_DECAY: float = 0.95
    MAX_LINEAGES: int = 5
    LINEAGE_SELECTION_INTERVAL: int = 10
    LINEAGE_MIN_AGE: int = 15
    DIVERSITY_NOISE: float = 0.0
    PHASE_TENSION_THRESHOLD_LOW_BASE: float = 0.002
    PHASE_TENSION_THRESHOLD_MID_BASE: float = 0.005
    PHASE_TENSION_THRESHOLD_HIGH_BASE: float = 0.015
    PHASE_UNKNOWN_DELTA_THRESHOLD: float = 0.015
    PHASE_BELIEF_LAG_THRESHOLD: float = 0.4
    SELF_MODEL_LEARNING_RATE: float = 0.15
    UNKNOWN_DECAY: float = 0.995
    UNKNOWN_BACKGROUND: float = 0.02
    UNKNOWN_DIVERGENCE_WEIGHT: float = 0.6
    CRISIS_MEMORY_DECAY: float = 0.90
    CRISIS_MEMORY_MAX: float = 0.8
    GIVEN_MODEL_SHAKE: float = 0.75
    GIVEN_MIN_AGE: int = 10
    GIVEN_COOLDOWN: int = 20
    GIVEN_SCAR_COST: float = 0.40
    NOVELTY_BONUS_WEIGHT: float = 0.2
    UNKNOWN_PENALTY_BASE: float = 0.15
    UNKNOWN_REDUCTION_BONUS: float = 0.1
    PERFECT_MODEL_PENALTY: float = 0.002
    GLOBAL_EVENT_COOLDOWN: int = 15
    HUNGER_MULTIPLIER: float = 1.8
    BOREDOM_WINDOW: int = 20
    MIN_PRED_ERROR: float = 0.005
    MIN_ACTIVE: float = 0.005
    MAX_METRIC: float = 2.0
    METRIC_DECAY: float = 0.99
    BASE_NOISE: float = 0.002
    COMPLACENCY_CONFIDENCE: float = 0.95
    COMPLACENCY_TENSION: float = 0.0005
    COMPLACENCY_THRESHOLD_SCALE: float = 0.7
    UNKNOWN_SPAWN_THRESHOLD: float = 0.25
    UNKNOWN_SPAWN_PROB: float = 0.01
    RESONANCE_DECAY: float = 0.95
    SOUL_CHECK_INTERVAL: int = 50
    SOUL_CHECK_NOISE: float = 0.001
    SOUL_TREMOR_STRENGTH: float = 0.3

    ENERGY_CONSERVATION_TOLERANCE = 1e-5
    ENERGY_INJECTION_RATE = 0.35
    FIELD_ENERGY_CLIP_MIN = -0.2
    FIELD_ENERGY_CLIP_MAX = 0.8
    ENERGY_CONSERVATION_VERBOSE = False

    SUBJECT_NARRATIVE_STABILITY_MAX: float = 0.95
    SUBJECT_MIN_NARRATIVE_VARIANCE: float = 0.02
    SUBJECT_MIN_SURPRISE_COUNT: int = 2
    SUBJECT_SELF_ERROR_MAX: float = 0.12
    SUBJECT_SPIRIT_GAP_MIN: float = 0.25

    MAX_CELLS_SOFT_LIMIT: int = 100
    MAX_CELLS_HARD_LIMIT: int = 130
    SIZE_TAX_RATE_SOFT: float = 0.05
    SIZE_TAX_RATE_HARD: float = 0.15

    OBS_GAP_CURIOSITY_THRESHOLD: float = 0.85
    OBS_GAP_CURIOSITY_BASE_PRIORITY: float = 2.0

    OBS_GAP_LOW_THRESHOLD: float = 0.5
    OBS_GAP_HIGH_THRESHOLD: float = 0.8
    HEARTBEAT_AMP_MIN: float = 0.002
    HEARTBEAT_AMP_MAX: float = 0.025
    SCAR_COUPLING_MIN: float = 0.001
    SCAR_COUPLING_MAX: float = 0.01
    ADAPT_CHAOS_SPEED: float = 0.35

    NOISE_GAIN_HIGH_THRESH: float = 1.2
    NOISE_GAIN_LOW_THRESH: float = 0.6
    NOISE_GAIN_MIN: float = 0.1
    NOISE_GAIN_SMOOTHING: float = 0.4

    EPISODIC_BUFFER_MAX_LEN: int = 3000

    VORTICITY_GAIN_MAX: float = 1.0
    VORTICITY_GAIN_MIN: float = 0.0
    NOISE_GAIN_MAX: float = 1.0
    NOISE_GAIN_MIN: float = 0.0
    PERCEPT_LOW_GAP: float = 0.2
    PERCEPT_HIGH_GAP: float = 0.8
    PERCEPT_ADAPT_SPEED: float = 0.1

    LABYRINTH_ADAPT_LOW_GAP: float = 0.3
    LABYRINTH_ADAPT_HIGH_GAP: float = 0.8
    LABYRINTH_ADAPT_MAX_MULT: float = 3.0
    LABYRINTH_ADAPT_SPEED: float = 0.1

    GIVEN_TENSION_TRIGGER: float = 0.4
    GIVEN_VETERAN_AGE: int = 100
    GIVEN_ROTATION_INTERVAL: int = 50

    MAX_BODY_CELLS: int = 300
    ANC_THRESHOLD: int = 300

    HEAL_WISDOM_AGE: int = 50
    HEAL_VETERAN_AGE: int = 100
    HEAL_ENLIGHTENED_AGE: int = 150

    SCAR_INJECTION_BASE_FACTOR: float = 1.5
    GIVEN_BASE_PROB_FACTOR: float = 1.4

    ARCHIVE_INHERIT_PROB: float = 0.2
    ARCHIVE_MAX_CONCEPTS: int = 2

    EXPLORE_FATIGUE_INTERVAL: int = 25
    EXPLORE_FATIGUE_AMOUNT: float = 0.015
    INTENT_SWITCH_REWARD_INSTANT: bool = True
    INTENT_SWITCH_GRATITUDE_BOOST: float = 0.015
    HEALTHY_SWITCH_OLD_INTENT: str = "explore"
    HEALTHY_SWITCH_NEW_INTENTS = ["cooperate", "seek_help", "rest"]
    WISDOM_AGE: int = 200
    WISDOM_HEALING_RATE: float = 0.999
    VETERAN_AGE_FOR_HEALING: int = 300
    ENLIGHTENED_AGE: int = 400
    ENLIGHTENED_COHERENCE_FLOOR: float = 0.6
    ENLIGHTENED_COHERENCE_FLOOR_FLEX: float = 0.85
    HEAL_WISDOM_BONUS: float = 0.025
    HEAL_VETERAN_BONUS: float = 0.035
    HEAL_ENLIGHTENED_BONUS: float = 0.040
    MUTATION_STRENGTH_BASE: float = 0.1
    SG_CRISIS_MUTATION_BOOST: float = 3.0

    # ============================================================
    # ДОБАВЛЕНО (24.07, слой "Ощущение / Самопричинность / Чужой разум /
    # Мета-слой / Незакрываемый вопрос") — см. обсуждение в чате про
    # эмерджентность и провал TOT_AGE/ANC (protection_level без затухания).
    # ============================================================

    # --- Фикс protection_level: щит был БЕССРОЧНЫМ (только max(), никогда
    # не убывал), из-за чего волна массового искупления (t~300-600) давала
    # синхронную "тихую" волну смертей ~150-200 тиков спустя (t~600-800) —
    # это и есть провал ANC/TOT_AGE. Теперь щит УГАСАЕТ: защита — это
    # отсрочка, а не бессрочный иммунитет, даже для самых древних линий.
    PROTECTION_DECAY_RATE: float = 0.99  # ~137 тиков до выхода из-под щита (0.8 -> <0.2)

    # --- Мета-слой: сам факт "я заметил(а), что снова думаю об этом" —
    # необратимая метка, не лечится обычным EPISTEMIC_HEALING_RATE.
    META_OBSERVATION_SCAR: float = 0.01

    # --- Незакрываемый вопрос: первый настоящий рекурсивный вопрос о себе
    # оставляет минимальный пол на unresolved_contradiction — ПОКА агент
    # держит свой root_question, contradiction не может схлопнуться
    # до death_no_contradiction (< 0.01). Порог заметно ниже дефолтного
    # рабочего диапазона (~0.3-0.5), так что это не отменяет угасание
    # контрадикции как механику — просто не даёт вопросу закрыться до нуля.
    UNCLOSABLE_QUESTION_FLOOR: float = 0.03

    # --- Чужой разум: порог "удивления" при неверном прогнозе состояния
    # доверенного соседа. Ниже порога — просто шум предсказания, выше —
    # настоящая инаковость другого, подпитывающая contradiction (а не
    # штрафующая agenta за неточность модели).
    OTHER_MIND_SURPRISE_THRESHOLD: float = 0.08

# ===== ОБНОВЛЁННЫЙ СЛОВАРЬ CH =====
CH = {
    'energy': 0, 'flux': 1, 'scar': 2, 'noise': 3, 'vorticity': 4,
    'owner': 5, 'surprise': 6, 'unknown': 7, 'event': 8, 'btype': 9,
    'crisis': 10, 'binding': 11,
    'signal_alarm': 12, 'signal_curiosity': 13, 'signal_warning': 14,
    'signal_invitation': 15, 'signal_gratitude': 16, 'signal_grief': 17,
    'intent_cooperate': 18, 'intent_explore': 19, 'intent_rest': 20, 'intent_seek_help': 21,
    'resonance': 22,
    'wall': 23,
    'signal_beauty': 24,
    'signal_rhythm': 25,
    'signal_interest': 26,
    'signal_memory': 27,
    'signal_silence': 28,
    'signal_sovereignty': 29,
    'signal_feral': 30,
    'signal_void': 31,
    'signal_introspection': 32,
}
# =================================================

@lru_cache(maxsize=8192)
def phi_hash_cached(x: int, y: int, seed: int) -> float:
    return ((x * Config.PHI + y * Config.PHI**2 + seed * Config.PHI**3) % 1.0)

def phi_hash(x, y, seed=0):
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        x_q = int(m.floor(x / 10.0) * 10) if abs(int(x)) > 100 else int(x)
        y_q = int(m.floor(y / 10.0) * 10) if abs(int(y)) > 100 else int(y)
        return phi_hash_cached(x_q, y_q, int(seed))
    return ((x * Config.PHI + y * Config.PHI**2 + seed * Config.PHI**3) % 1.0)

def phi_noise(t, x, y, seed=0):
    return (phi_hash(t + x, y + t, seed) - 0.5) * 0.1

def deterministic_noise(t, x, y, scale=0.01):
    return phi_noise(t, x, y, Config.DETERMINISTIC_SEED) * scale

def squash(x):
    if np.isnan(x) or np.isinf(x): return 0.5
    return np.clip(x / (1.0 + abs(x)), -1.0, 1.0)

# КОНСОЛИДИРОВАНО: раньше safe_mean переопределялась 4 раза в разных ячейках
# с разным default (0.0/0.5) и разной защитой от нечисловых значений.
# Побеждала всегда только последняя по файлу версия — при ручном перезапуске
# ячеек не по порядку функция могла тихо откатиться к слабой реализации без
# предупреждения. Теперь она определена один раз, здесь, с самой надёжной
# реализацией (переживает dict/None/мусор в списке, не падает с TypeError).
def safe_mean(vals, default=0.0):
    try:
        arr = np.asarray(vals, dtype=np.float64).flatten()
    except (TypeError, ValueError):
        cleaned = []
        try:
            iterable = list(vals)
        except TypeError:
            iterable = [vals]
        for v in iterable:
            try:
                fv = float(v)
                if np.isfinite(fv):
                    cleaned.append(fv)
            except (TypeError, ValueError):
                continue
        return float(np.mean(cleaned)) if cleaned else float(default)
    mask = np.isfinite(arr)
    if mask.any():
        return float(np.mean(arr[mask]))
    return float(default)

def _emotional_decay_factor(age, base_rate=None):
    if base_rate is None: base_rate = Config.EMOTIONAL_DECAY_RATE_BASE
    age_factor = 1.0 - 0.3 * np.tanh(age / 200.0)
    return base_rate ** age_factor

def _safe_emotional_decay(mem_dict, key, age):
    val = mem_dict.get(key, 0.0)
    if not np.isfinite(val): val = 0.0
    decay = _emotional_decay_factor(age)
    mem_dict[key] = float(np.clip(val * decay, 0.0, 1.0))

print("✅ Ячейка 0.1 загружена: ПОЛНЫЙ Config (применён патч 1: лабиринт и крик).")