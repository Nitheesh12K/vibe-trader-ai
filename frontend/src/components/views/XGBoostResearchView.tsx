import React, { useState, useEffect } from 'react';
import {
  Brain,
  Cpu,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Sliders,
  Play,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Info,
  Layers,
  Sparkles,
  Clock,
  ChevronRight,
  Database,
  Crosshair,
  ArrowRight,
  GitCompare,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  NavTabId,
  XGBoostModelSummary,
  XGBoostModelDetail,
  XGBoostTrainResponse,
  XGBoostPredictResponse,
  XGBoostPredictionRecordItem,
  XGBoostSynthesizeResponse,
  AIComparisonSummaryData,
  AIStrategyComparisonRecordItem,
} from '../../types/market';

interface XGBoostResearchViewProps {
  onNavigate?: (tab: NavTabId) => void;
}

export const XGBoostResearchView: React.FC<XGBoostResearchViewProps> = ({ onNavigate }) => {
  // Model training state
  const [symbol, setSymbol] = useState<string>('RELIANCE');
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [trainRatio, setTrainRatio] = useState<number>(0.7);
  const [valRatio, setValRatio] = useState<number>(0.15);
  const [testRatio, setTestRatio] = useState<number>(0.15);
  const [nEstimators, setNEstimators] = useState<number>(100);
  const [maxDepth, setMaxDepth] = useState<number>(4);
  const [learningRate, setLearningRate] = useState<number>(0.05);
  const [earlyStopping, setEarlyStopping] = useState<number>(10);
  const [cvFolds, setCvFolds] = useState<number>(3);

  // UI state
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [trainingError, setTrainingError] = useState<string | null>(null);
  const [trainingSuccess, setTrainingSuccess] = useState<string | null>(null);

  // Models list & active detail
  const [models, setModels] = useState<XGBoostModelSummary[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [activeModelDetail, setActiveModelDetail] = useState<XGBoostModelDetail | null>(null);
  const [loadingModels, setLoadingModels] = useState<boolean>(false);

  // Prediction state
  const [isPredicting, setIsPredicting] = useState<boolean>(false);
  const [predictionResult, setPredictionResult] = useState<XGBoostPredictResponse | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [predictionsHistory, setPredictionsHistory] = useState<XGBoostPredictionRecordItem[]>([]);

  // Qwen Synthesis state
  const [ruleSignal, setRuleSignal] = useState<'BUY' | 'SELL' | 'HOLD'>('BUY');
  const [ruleConfidence, setRuleConfidence] = useState<number>(0.75);
  const [ruleReasoning, setRuleReasoning] = useState<string>(
    'EMA 9/21 bullish crossover with RSI at 54 and positive MACD histogram expansion.'
  );
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);
  const [synthesizeResult, setSynthesizeResult] = useState<XGBoostSynthesizeResponse | null>(null);
  const [synthesizeError, setSynthesizeError] = useState<string | null>(null);

  // AI vs Deterministic Comparison state
  const [comparisonSummary, setComparisonSummary] = useState<AIComparisonSummaryData | null>(null);
  const [comparisonFilter, setComparisonFilter] = useState<string>('ALL');
  const [loadingComparison, setLoadingComparison] = useState<boolean>(false);

  // Initial load
  useEffect(() => {
    loadModels();
    loadPredictionHistory();
  }, []);

  useEffect(() => {
    loadComparisonSummary();
  }, [comparisonFilter]);

  const loadComparisonSummary = async () => {
    try {
      setLoadingComparison(true);
      const res = await api.getAIComparisonSummary({
        concurrence_status: comparisonFilter === 'ALL' ? undefined : comparisonFilter,
        limit: 15,
      });
      setComparisonSummary(res);
    } catch (err: any) {
      console.error('Failed to load AI comparison summary:', err);
    } finally {
      setLoadingComparison(false);
    }
  };

  const loadModels = async () => {
    try {
      setLoadingModels(true);
      const res = await api.getXGBoostModels();
      setModels(res);
      if (res.length > 0 && !selectedModelId) {
        await handleSelectModel(res[0].model_id);
      }
    } catch (err: any) {
      console.error('Failed to load XGBoost models:', err);
    } finally {
      setLoadingModels(false);
    }
  };

  const loadPredictionHistory = async () => {
    try {
      const res = await api.getXGBoostPredictions(undefined, 10);
      setPredictionsHistory(res);
    } catch (err: any) {
      console.error('Failed to load predictions history:', err);
    }
  };

  const handleSelectModel = async (modelId: string) => {
    try {
      setSelectedModelId(modelId);
      const detail = await api.getXGBoostModelDetail(modelId);
      setActiveModelDetail(detail);
    } catch (err: any) {
      console.error('Failed to load model details:', err);
    }
  };

  const handleTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsTraining(true);
    setTrainingError(null);
    setTrainingSuccess(null);

    try {
      const res: XGBoostTrainResponse = await api.trainXGBoost({
        symbol,
        timeframe,
        train_ratio: trainRatio,
        val_ratio: valRatio,
        test_ratio: testRatio,
        n_estimators: nEstimators,
        max_depth: maxDepth,
        learning_rate: learningRate,
        early_stopping_rounds: earlyStopping,
        cv_folds: cvFolds,
        random_state: 42,
      });

      setTrainingSuccess(`Model ${res.model_id} trained successfully! Test Accuracy: ${(res.metrics.test.accuracy * 100).toFixed(1)}%`);
      await loadModels();
      await handleSelectModel(res.model_id);
    } catch (err: any) {
      setTrainingError(err.message || 'Failed to train XGBoost model');
    } finally {
      setIsTraining(false);
    }
  };

  const handlePredict = async () => {
    setIsPredicting(true);
    setPredictionError(null);

    try {
      const res = await api.predictXGBoost({
        symbol,
        timeframe,
        model_id: selectedModelId || undefined,
      });
      setPredictionResult(res);
      await loadPredictionHistory();
    } catch (err: any) {
      setPredictionError(err.message || 'Failed to generate advisory prediction');
    } finally {
      setIsPredicting(false);
    }
  };

  const handleSynthesize = async () => {
    setIsSynthesizing(true);
    setSynthesizeError(null);

    try {
      const res = await api.synthesizeXGBoost({
        symbol,
        timeframe,
        model_id: selectedModelId || undefined,
        rule_signal: ruleSignal,
        confidence: ruleConfidence,
        proposed_reasoning: ruleReasoning,
      });
      setSynthesizeResult(res);
      // Auto-record comparison between deterministic rule and AI/XGBoost output
      try {
        await api.evaluateAIComparison({
          symbol,
          timeframe,
          deterministic_strategy_name: 'SYNTHESIS_FORM_RULE',
          deterministic_signal: ruleSignal,
          deterministic_confidence: ruleConfidence,
          xgboost_predicted_direction: res.xgboost_prediction.includes('BULLISH') ? 'UP' : res.xgboost_prediction.includes('BEARISH') ? 'DOWN' : 'ABSTAIN',
          xgboost_probability: res.probability_up,
          qwen_synthesized_recommendation: res.synthesized_recommendation.includes('BUY') ? 'BUY' : res.synthesized_recommendation.includes('SELL') ? 'SELL' : 'HOLD',
          notes: 'Auto-recorded from interactive XGBoost + Qwen research synthesis',
        });
        await loadComparisonSummary();
      } catch (recErr) {
        console.warn('Auto comparison recording note:', recErr);
      }
    } catch (err: any) {
      setSynthesizeError(err.message || 'Failed to synthesize advisory insight');
    } finally {
      setIsSynthesizing(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Header & Non-Negotiable Research Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
                XGBoost Quantitative Research Engine
                <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-500/20 border border-amber-500/40 text-amber-300">
                  Advisory Mode
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Machine learning research environment for next-bar directional forecasting, causal indicators, and walk-forward validation.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadModels}
            disabled={loadingModels}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-medium transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingModels ? 'animate-spin' : ''}`} />
            Refresh Models
          </button>
        </div>
      </div>

      {/* Mandatory Safety Notice */}
      <div className="bg-amber-950/30 border border-amber-500/40 rounded-xl p-4 flex items-start gap-3.5 backdrop-blur-sm">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <span className="font-bold text-amber-300 uppercase tracking-wider block">
            RESEARCH ADVISORY ONLY — NOT A TRADE INSTRUCTION
          </span>
          <p className="text-amber-200/80 leading-relaxed">
            XGBoost model predictions and Qwen advisory syntheses are purely experimental research tools.
            They operate strictly out-of-band and <strong>NEVER execute orders directly</strong>, alter portfolio balances, or bypass the deterministic Risk Guardian and human BUY approval gate. Live broker endpoints remain fail-closed.
          </p>
        </div>
      </div>

      {/* Main Grid: Training Config & Model Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Model Training & Experiment Config */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl">
            <h2 className="text-sm font-bold text-white flex items-center gap-2 mb-4">
              <Sliders className="w-4 h-4 text-purple-400" />
              Train Model Experiment
            </h2>

            <form onSubmit={handleTrain} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Target Symbol</label>
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="RELIANCE">RELIANCE (NSE Daily Data)</option>
                  <option value="TATASTEEL">TATASTEEL (NSE Daily Data)</option>
                  <option value="NIFTY 50">NIFTY 50</option>
                  <option value="BANKNIFTY">BANKNIFTY</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Timeframe</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="1D">1D (Daily)</option>
                    <option value="1h">1h (Hourly)</option>
                    <option value="15m">15m</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">CV Folds (Walk-Forward)</label>
                  <input
                    type="number"
                    min={2}
                    max={10}
                    value={cvFolds}
                    onChange={(e) => setCvFolds(parseInt(e.target.value) || 3)}
                    className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              {/* Chronological Split Ratios */}
              <div className="p-3 bg-white/[0.02] border border-white/[0.05] rounded-lg space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Temporal Split Ratios (No Shuffling)
                </span>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div>
                    <label className="text-[10px] text-slate-400">Train</label>
                    <input
                      type="number"
                      step={0.05}
                      min={0.5}
                      max={0.85}
                      value={trainRatio}
                      onChange={(e) => setTrainRatio(parseFloat(e.target.value) || 0.7)}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded px-2 py-1 text-center text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Val</label>
                    <input
                      type="number"
                      step={0.05}
                      min={0.05}
                      max={0.3}
                      value={valRatio}
                      onChange={(e) => setValRatio(parseFloat(e.target.value) || 0.15)}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded px-2 py-1 text-center text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Test</label>
                    <input
                      type="number"
                      step={0.05}
                      min={0.05}
                      max={0.3}
                      value={testRatio}
                      onChange={(e) => setTestRatio(parseFloat(e.target.value) || 0.15)}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded px-2 py-1 text-center text-xs text-white"
                    />
                  </div>
                </div>
              </div>

              {/* Hyperparameters */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Max Depth</label>
                  <input
                    type="number"
                    min={2}
                    max={10}
                    value={maxDepth}
                    onChange={(e) => setMaxDepth(parseInt(e.target.value) || 4)}
                    className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Learning Rate (η)</label>
                  <input
                    type="number"
                    step={0.01}
                    min={0.01}
                    max={0.5}
                    value={learningRate}
                    onChange={(e) => setLearningRate(parseFloat(e.target.value) || 0.05)}
                    className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Estimators</label>
                  <input
                    type="number"
                    min={10}
                    max={500}
                    value={nEstimators}
                    onChange={(e) => setNEstimators(parseInt(e.target.value) || 100)}
                    className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Early Stopping</label>
                  <input
                    type="number"
                    min={2}
                    max={50}
                    value={earlyStopping}
                    onChange={(e) => setEarlyStopping(parseInt(e.target.value) || 10)}
                    className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              {trainingError && (
                <div className="p-3 bg-red-950/40 border border-red-500/40 rounded-lg text-xs text-red-300 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{trainingError}</span>
                </div>
              )}

              {trainingSuccess && (
                <div className="p-3 bg-emerald-950/40 border border-emerald-500/40 rounded-lg text-xs text-emerald-300 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{trainingSuccess}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isTraining}
                className="w-full py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-purple-900/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {isTraining ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Training Causal XGBoost...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Training Pipeline
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Model Registry List */}
          <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl">
            <h2 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-cyan-400" />
              Trained Model Artifacts ({models.length})
            </h2>

            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {models.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No trained models yet. Train your first experiment above.</p>
              ) : (
                models.map((m) => (
                  <button
                    key={m.model_id}
                    onClick={() => handleSelectModel(m.model_id)}
                    className={`w-full text-left p-2.5 rounded-lg border transition-all text-xs flex items-center justify-between ${
                      selectedModelId === m.model_id
                        ? 'bg-purple-950/40 border-purple-500/50 text-white'
                        : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:bg-white/[0.05]'
                    }`}
                  >
                    <div>
                      <div className="font-semibold text-white flex items-center gap-2">
                        {m.symbol} ({m.timeframe})
                        <span className="text-[10px] text-slate-400 font-mono">
                          {m.model_id.substring(0, 16)}...
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Accuracy: <span className="text-emerald-400 font-mono">{(((m.test_accuracy ?? (m as any).out_of_sample_accuracy) != null ? Number(m.test_accuracy ?? (m as any).out_of_sample_accuracy) : 0) * 100).toFixed(1)}%</span> | F1: <span className="font-mono">{((m.test_f1 ?? (m as any).out_of_sample_f1) != null ? Number(m.test_f1 ?? (m as any).out_of_sample_f1) : 0).toFixed(3)}</span>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Model Metrics, Feature Importance, Baselines */}
        <div className="lg:col-span-8 space-y-6">
          {activeModelDetail ? (
            <>
              {/* Performance Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-4 backdrop-blur-xl">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Out-of-Sample Accuracy
                  </span>
                  <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                    {((activeModelDetail.test_metrics?.accuracy ?? (activeModelDetail as any).out_of_sample_metrics?.accuracy ?? 0) * 100).toFixed(1)}%
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Balanced: {((activeModelDetail.test_metrics?.balanced_accuracy ?? (activeModelDetail as any).out_of_sample_metrics?.balanced_accuracy ?? 0) * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-4 backdrop-blur-xl">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Test F1-Score
                  </span>
                  <div className="text-2xl font-bold font-mono text-purple-400 mt-1">
                    {(activeModelDetail.test_metrics?.f1 ?? (activeModelDetail as any).out_of_sample_metrics?.f1 ?? 0).toFixed(3)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Precision: {(activeModelDetail.test_metrics?.precision ?? (activeModelDetail as any).out_of_sample_metrics?.precision ?? 0).toFixed(2)} | Recall: {(activeModelDetail.test_metrics?.recall ?? (activeModelDetail as any).out_of_sample_metrics?.recall ?? 0).toFixed(2)}
                  </div>
                </div>

                <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-4 backdrop-blur-xl">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    ROC-AUC
                  </span>
                  <div className="text-2xl font-bold font-mono text-sky-400 mt-1">
                    {(activeModelDetail.test_metrics?.roc_auc ?? (activeModelDetail as any).out_of_sample_metrics?.roc_auc) != null
                      ? Number(activeModelDetail.test_metrics?.roc_auc ?? (activeModelDetail as any).out_of_sample_metrics?.roc_auc).toFixed(3)
                      : 'N/A'}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Log Loss: {(activeModelDetail.test_metrics?.log_loss ?? (activeModelDetail as any).out_of_sample_metrics?.log_loss ?? 0).toFixed(3)}
                  </div>
                </div>

                <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-4 backdrop-blur-xl">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Brier Score (Calibration)
                  </span>
                  <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                    {(activeModelDetail.test_metrics?.brier_score ?? (activeModelDetail as any).out_of_sample_metrics?.brier_score ?? (activeModelDetail as any).calibration_metrics?.brier_score ?? 0).toFixed(3)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Lower is better (0 = ideal)
                  </div>
                </div>
              </div>

              {/* Baseline Comparison Card */}
              <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl">
                <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
                  <BarChart3 className="w-4 h-4 text-emerald-400" />
                  Comparison with Naive Benchmark Baselines
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-lg">
                    <span className="font-semibold text-purple-300 block mb-1">XGBoost (Active Model)</span>
                    <div className="text-slate-300">Accuracy: <span className="font-mono text-emerald-400">{((activeModelDetail.test_metrics?.accuracy ?? (activeModelDetail as any).out_of_sample_metrics?.accuracy ?? 0) * 100).toFixed(1)}%</span></div>
                    <div className="text-slate-400">Brier Score: <span className="font-mono text-amber-400">{(activeModelDetail.test_metrics?.brier_score ?? (activeModelDetail as any).out_of_sample_metrics?.brier_score ?? 0).toFixed(3)}</span></div>
                  </div>

                  <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-lg">
                    <span className="font-semibold text-slate-300 block mb-1">Majority Class Baseline</span>
                    <div className="text-slate-300">Accuracy: <span className="font-mono">{((activeModelDetail.baseline_metrics?.majority_class?.accuracy ?? (activeModelDetail.baseline_metrics as any)?.majority_class_baseline?.accuracy ?? 0) * 100).toFixed(1)}%</span></div>
                    <div className="text-slate-400">Brier Score: <span className="font-mono">{(activeModelDetail.baseline_metrics?.majority_class?.brier_score ?? (activeModelDetail.baseline_metrics as any)?.majority_class_baseline?.brier_score ?? 0.25).toFixed(3)}</span></div>
                  </div>

                  <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-lg">
                    <span className="font-semibold text-slate-300 block mb-1">Momentum Direction Baseline</span>
                    <div className="text-slate-300">Accuracy: <span className="font-mono">{((activeModelDetail.baseline_metrics?.momentum?.accuracy ?? (activeModelDetail.baseline_metrics as any)?.momentum_direction_baseline?.accuracy ?? 0) * 100).toFixed(1)}%</span></div>
                    <div className="text-slate-400">Brier Score: <span className="font-mono">{(activeModelDetail.baseline_metrics?.momentum?.brier_score ?? (activeModelDetail.baseline_metrics as any)?.momentum_direction_baseline?.brier_score ?? 0.25).toFixed(3)}</span></div>
                  </div>
                </div>
              </div>

              {/* Feature Importance & Confusion Matrix */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Feature Importance Bars */}
                <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    Causal Feature Importance (Gain)
                  </h3>
                  <div className="space-y-2.5 text-xs">
                    {(() => {
                      const featList = activeModelDetail.feature_importances || [];
                      const maxGain = Math.max(...featList.map((x) => x.gain || 0), 0.001);
                      if (featList.length === 0) {
                        return <p className="text-slate-500 italic text-xs">No feature importance data available.</p>;
                      }
                      return featList.map((f) => {
                        const pct = Math.min(100, Math.round(((f.gain || 0) / maxGain) * 100));
                        return (
                          <div key={f.feature_name}>
                            <div className="flex justify-between text-slate-300 mb-1">
                              <span className="font-mono text-[11px]">{f.feature_name}</span>
                              <span className="font-mono text-purple-300">{(f.gain || 0).toFixed(4)}</span>
                            </div>
                            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-purple-600 to-indigo-500 rounded-full"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      });
                    })()}
                  </div>
                </div>

                {/* Confusion Matrix & Walk-Forward Folds */}
                <div className="space-y-6">
                  <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
                      <Crosshair className="w-4 h-4 text-cyan-400" />
                      Test Confusion Matrix
                    </h3>
                    <div className="overflow-x-auto text-xs">
                      <table className="w-full text-center border-collapse">
                        <thead>
                          <tr className="border-b border-white/10 text-slate-400">
                            <th className="p-2 text-left">Actual \ Pred</th>
                            <th className="p-2">Pred Down (0)</th>
                            <th className="p-2">Pred Up (1)</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr className="border-b border-white/[0.05]">
                            <td className="p-2 text-left text-slate-300 font-semibold">Actual Down (0)</td>
                            <td className="p-2 font-mono font-bold text-slate-200">
                              {activeModelDetail.test_metrics?.confusion_matrix?.[0]?.[0] ?? (activeModelDetail as any).confusion_matrix?.true_negatives ?? 0}
                            </td>
                            <td className="p-2 font-mono text-red-400">
                              {activeModelDetail.test_metrics?.confusion_matrix?.[0]?.[1] ?? (activeModelDetail as any).confusion_matrix?.false_positives ?? 0}
                            </td>
                          </tr>
                          <tr>
                            <td className="p-2 text-left text-slate-300 font-semibold">Actual Up (1)</td>
                            <td className="p-2 font-mono text-amber-400">
                              {activeModelDetail.test_metrics?.confusion_matrix?.[1]?.[0] ?? (activeModelDetail as any).confusion_matrix?.false_negatives ?? 0}
                            </td>
                            <td className="p-2 font-mono font-bold text-emerald-400">
                              {activeModelDetail.test_metrics?.confusion_matrix?.[1]?.[1] ?? (activeModelDetail as any).confusion_matrix?.true_positives ?? 0}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Walk-Forward Folds */}
                  <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
                      <Layers className="w-4 h-4 text-sky-400" />
                      Walk-Forward Validation Folds ({activeModelDetail.walk_forward_results?.length ?? (activeModelDetail as any).walk_forward_metrics?.length ?? 0})
                    </h3>
                    <div className="space-y-1.5 text-xs max-h-36 overflow-y-auto">
                      {(activeModelDetail.walk_forward_results || []).map((f) => (
                        <div
                          key={f.fold}
                          className="flex items-center justify-between p-2 rounded bg-white/[0.02] border border-white/[0.04]"
                        >
                          <span className="font-semibold text-slate-300">Fold #{f.fold}</span>
                          <span className="text-slate-400 font-mono text-[11px]">
                            {f.train_samples} tr / {f.test_samples} te
                          </span>
                          <span className="font-mono text-emerald-400 font-bold">
                            {((f.test_accuracy ?? 0) * 100).toFixed(1)}% Acc
                          </span>
                          <span className="font-mono text-purple-400">
                            F1: {(f.test_f1 ?? f.test_accuracy ?? 0).toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-12 text-center backdrop-blur-xl text-slate-400">
              <Cpu className="w-12 h-12 mx-auto mb-3 text-slate-600 animate-pulse" />
              <p className="text-sm font-medium">Select a model artifact on the left or train a new one to inspect out-of-sample metrics.</p>
            </div>
          )}
        </div>
      </div>

      {/* Advisory Inference & Qwen Synthesis Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Advisory Directional Inference */}
        <div className="lg:col-span-6 bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Crosshair className="w-4 h-4 text-purple-400" />
              Real-Time Next-Bar Advisory Inference
            </h2>
            <button
              onClick={handlePredict}
              disabled={isPredicting || !selectedModelId}
              className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              {isPredicting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Forecast Next Bar
            </button>
          </div>

          <p className="text-xs text-slate-400">
            Computes causal features strictly from historical bars ending at $t$ and evaluates next-bar ($t+1$) directional probability using the selected model.
          </p>

          {predictionError && (
            <div className="p-3 bg-red-950/40 border border-red-500/40 rounded-lg text-xs text-red-300 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{predictionError}</span>
            </div>
          )}

          {predictionResult && (
            <div className="space-y-4 pt-2">
              {/* Probability Meter */}
              <div className="p-4 bg-white/[0.02] border border-white/[0.06] rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300">Predicted Direction:</span>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                      predictionResult.predicted_direction?.includes('BULL')
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : predictionResult.predicted_direction?.includes('BEAR')
                        ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                        : 'bg-slate-500/20 text-slate-400 border border-slate-500/40'
                    }`}
                  >
                    {predictionResult.predicted_direction}
                  </span>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Down: {(((predictionResult.probability_down ?? (predictionResult as any).bearish_probability) ?? 0) * 100).toFixed(1)}%</span>
                    <span>Confidence: {(((predictionResult.confidence ?? (predictionResult as any).predicted_probability) ?? 0) * 100).toFixed(1)}%</span>
                    <span>Up: {(((predictionResult.probability_up ?? (predictionResult as any).bullish_probability) ?? 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-3 bg-red-500/20 rounded-full overflow-hidden flex">
                    <div
                      className="h-full bg-red-500 transition-all duration-500"
                      style={{ width: `${((predictionResult.probability_down ?? (predictionResult as any).bearish_probability) ?? 0) * 100}%` }}
                    />
                    <div
                      className="h-full bg-emerald-500 transition-all duration-500"
                      style={{ width: `${((predictionResult.probability_up ?? (predictionResult as any).bullish_probability) ?? 0) * 100}%` }}
                    />
                  </div>
                </div>

                {predictionResult.warning && (
                  <div className="text-[11px] text-amber-300/90 bg-amber-950/20 border border-amber-500/30 rounded p-2">
                    {predictionResult.warning}
                  </div>
                )}
              </div>

              {/* Top Feature Contributions */}
              {((predictionResult.top_contributing_features?.length ?? 0) > 0 || (predictionResult as any).features_snapshot) && (
                <div>
                  <span className="text-xs font-semibold text-slate-300 block mb-2">
                    Top Contributing Features (Local Approximation):
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {(predictionResult.top_contributing_features || []).map((feat) => (
                      <div key={feat.feature_name} className="p-2 bg-white/[0.02] border border-white/[0.04] rounded">
                        <div className="text-slate-400 text-[10px]">{feat.feature_name}</div>
                        <div className="font-mono text-white text-[11px]">
                          Val: {(feat.value || 0).toFixed(3)} | Impact: {(feat.contribution_score || 0).toFixed(3)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Qwen + Rule-Based Advisory Synthesis */}
        <div className="lg:col-span-6 bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Qwen + XGBoost Advisory Synthesis
            </h2>
            <button
              onClick={handleSynthesize}
              disabled={isSynthesizing}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              {isSynthesizing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Synthesize Advisory
            </button>
          </div>

          <p className="text-xs text-slate-400">
            Synthesizes rule-based candidate signals with XGBoost directional forecasts using Qwen (with deterministic fallback).
          </p>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Rule Signal</label>
              <select
                value={ruleSignal}
                onChange={(e) => setRuleSignal(e.target.value as any)}
                className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="BUY">BUY Signal</option>
                <option value="SELL">SELL Signal</option>
                <option value="HOLD">HOLD Signal</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Rule Confidence</label>
              <input
                type="number"
                step={0.05}
                min={0.1}
                max={1.0}
                value={ruleConfidence}
                onChange={(e) => setRuleConfidence(parseFloat(e.target.value) || 0.7)}
                className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Proposed Strategy Reasoning</label>
            <textarea
              rows={2}
              value={ruleReasoning}
              onChange={(e) => setRuleReasoning(e.target.value)}
              className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>

          {synthesizeError && (
            <div className="p-3 bg-red-950/40 border border-red-500/40 rounded-lg text-xs text-red-300 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{synthesizeError}</span>
            </div>
          )}

          {synthesizeResult && (
            <div className="space-y-3 pt-2 text-xs">
              {synthesizeResult.divergence_detected && (
                <div className="p-3 bg-amber-950/40 border border-amber-500/50 rounded-xl text-amber-200 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-amber-300 uppercase">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    Divergence Detected!
                  </div>
                  <p className="text-[11px]">{synthesizeResult.divergence_warning}</p>
                </div>
              )}

              <div className="p-4 bg-white/[0.02] border border-white/[0.06] rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Synthesized Recommendation:</span>
                  <span className="font-bold text-white uppercase">
                    {synthesizeResult.synthesized_recommendation || (synthesizeResult as any).synthesis?.synthesis_verdict || 'NEUTRAL'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Unified Confidence:</span>
                  <span className="font-mono text-purple-400 font-bold">
                    {((synthesizeResult.unified_confidence ?? (synthesizeResult as any).synthesis?.unified_confidence ?? 0.75) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="pt-2 border-t border-white/[0.06]">
                  <span className="font-semibold text-slate-300 block mb-1">Advisory Reasoning:</span>
                  <p className="text-slate-300 leading-relaxed italic bg-black/20 p-3 rounded-lg border border-white/[0.04]">
                    "{synthesizeResult.qwen_advisory_text || (synthesizeResult as any).synthesis?.ai_explanation || 'Advisory synthesis evaluated.'}"
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Historical Advisory Predictions Table */}
      <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl">
        <h2 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
          <Clock className="w-4 h-4 text-slate-400" />
          Recent Advisory Predictions Log ({predictionsHistory.length})
        </h2>

        <div className="overflow-x-auto text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-slate-400">
                <th className="p-2">ID</th>
                <th className="p-2">Timestamp</th>
                <th className="p-2">Symbol</th>
                <th className="p-2">Direction</th>
                <th className="p-2">P(Up)</th>
                <th className="p-2">Confidence</th>
                <th className="p-2">Actual Next Bar</th>
                <th className="p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {predictionsHistory.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-4 text-center text-slate-500 italic">
                    No advisory predictions recorded yet.
                  </td>
                </tr>
              ) : (
                predictionsHistory.map((rec) => (
                  <tr key={rec.id ?? (rec as any).prediction_id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                    <td className="p-2 font-mono text-slate-400">#{rec.id ?? (rec as any).prediction_id}</td>
                    <td className="p-2 text-slate-300">{rec.prediction_timestamp}</td>
                    <td className="p-2 font-semibold text-white">{rec.symbol}</td>
                    <td className="p-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          rec.predicted_direction?.includes('BULL')
                            ? 'text-emerald-400 bg-emerald-500/10'
                            : rec.predicted_direction?.includes('BEAR')
                            ? 'text-red-400 bg-red-500/10'
                            : 'text-slate-400 bg-slate-500/10'
                        }`}
                      >
                        {rec.predicted_direction}
                      </span>
                    </td>
                    <td className="p-2 font-mono text-slate-300">{(((rec.probability_up ?? (rec as any).bullish_probability) ?? 0) * 100).toFixed(1)}%</td>
                    <td className="p-2 font-mono text-slate-300">{(((rec.confidence ?? (rec as any).predicted_probability) ?? 0) * 100).toFixed(1)}%</td>
                    <td className="p-2 font-mono text-slate-400">{rec.actual_direction || '—'}</td>
                    <td className="p-2">
                      {rec.is_correct === true ? (
                        <span className="text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Correct
                        </span>
                      ) : rec.is_correct === false ? (
                        <span className="text-red-400 flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5" /> Incorrect
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Unverified (Pending)</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI vs Deterministic Strategy Concurrence & Divergence Evaluation */}
      <div className="bg-[#111726]/80 border border-white/[0.08] rounded-xl p-5 backdrop-blur-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-purple-400" />
              AI vs Deterministic Strategy Concurrence & Divergence
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Tracks concurrence, divergence alerts, and failure prevention between rule-based technical signals and AI/ML advisories.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Filter buttons */}
            <div className="flex rounded-lg bg-black/40 p-0.5 border border-white/10 text-[11px]">
              {(['ALL', 'AGREE', 'DIVERGE', 'CAUTIONARY'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setComparisonFilter(mode)}
                  className={`px-2.5 py-1 rounded font-medium transition-all ${
                    comparisonFilter === mode
                      ? 'bg-purple-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>

            <button
              onClick={loadComparisonSummary}
              disabled={loadingComparison}
              className="p-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 text-xs transition-colors"
              title="Refresh comparison records"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingComparison ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Metrics Summary Cards */}
        {comparisonSummary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl">
              <span className="text-[11px] text-slate-400 block">Total Evaluations</span>
              <span className="text-lg font-bold text-white font-mono">{comparisonSummary.total_records}</span>
            </div>
            <div className="p-3 bg-emerald-500/[0.04] border border-emerald-500/20 rounded-xl">
              <span className="text-[11px] text-emerald-400 block">Agreement Rate</span>
              <span className="text-lg font-bold text-emerald-400 font-mono">
                {(comparisonSummary.agreement_rate * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                ({comparisonSummary.agreement_count} aligned)
              </span>
            </div>
            <div className="p-3 bg-red-500/[0.04] border border-red-500/20 rounded-xl">
              <span className="text-[11px] text-red-400 block">Divergence Rate</span>
              <span className="text-lg font-bold text-red-400 font-mono">
                {(comparisonSummary.divergence_rate * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                ({comparisonSummary.divergence_count} flagged)
              </span>
            </div>
            <div className="p-3 bg-amber-500/[0.04] border border-amber-500/20 rounded-xl">
              <span className="text-[11px] text-amber-400 block">Cautionary Rate</span>
              <span className="text-lg font-bold text-amber-400 font-mono">
                {(comparisonSummary.cautionary_rate * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                ({comparisonSummary.cautionary_count} caution)
              </span>
            </div>
          </div>
        )}

        {/* Comparison Records Table */}
        <div className="overflow-x-auto text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-slate-400">
                <th className="p-2">Record ID</th>
                <th className="p-2">Symbol</th>
                <th className="p-2">Deterministic Strategy</th>
                <th className="p-2">Deterministic Signal</th>
                <th className="p-2">XGBoost Prob</th>
                <th className="p-2">Qwen Rec</th>
                <th className="p-2">Concurrence Status</th>
                <th className="p-2">Divergence Reason / Notes</th>
              </tr>
            </thead>
            <tbody>
              {!comparisonSummary || comparisonSummary.records.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-4 text-center text-slate-500 italic">
                    {loadingComparison ? 'Loading comparison records...' : 'No comparison records found for this filter.'}
                  </td>
                </tr>
              ) : (
                comparisonSummary.records.map((r) => (
                  <tr key={r.record_id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                    <td className="p-2 font-mono text-slate-400">{r.record_id}</td>
                    <td className="p-2 font-semibold text-white">{r.symbol} ({r.timeframe})</td>
                    <td className="p-2 text-slate-300">{r.deterministic_strategy_name}</td>
                    <td className="p-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.deterministic_signal === 'BUY'
                            ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/30'
                            : r.deterministic_signal === 'SELL'
                            ? 'text-red-400 bg-red-500/10 border border-red-500/30'
                            : 'text-slate-400 bg-slate-500/10 border border-slate-500/30'
                        }`}
                      >
                        {r.deterministic_signal}
                      </span>
                    </td>
                    <td className="p-2 font-mono text-slate-300">
                      {r.xgboost_probability !== null && r.xgboost_probability !== undefined
                        ? `${(r.xgboost_probability * 100).toFixed(1)}% (${r.xgboost_predicted_direction || 'N/A'})`
                        : '—'}
                    </td>
                    <td className="p-2 font-semibold text-indigo-300">
                      {r.qwen_synthesized_recommendation || '—'}
                    </td>
                    <td className="p-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 w-fit ${
                          r.concurrence_status === 'AGREE'
                            ? 'text-emerald-400 bg-emerald-500/20 border border-emerald-500/40'
                            : r.concurrence_status === 'DIVERGE'
                            ? 'text-red-400 bg-red-500/20 border border-red-500/40'
                            : 'text-amber-400 bg-amber-500/20 border border-amber-500/40'
                        }`}
                      >
                        {r.concurrence_status === 'AGREE' && <CheckCircle2 className="w-3 h-3" />}
                        {r.concurrence_status === 'DIVERGE' && <AlertTriangle className="w-3 h-3" />}
                        {r.concurrence_status === 'CAUTIONARY' && <Info className="w-3 h-3" />}
                        {r.concurrence_status}
                      </span>
                    </td>
                    <td className="p-2 text-slate-400 max-w-xs truncate" title={r.divergence_reason || r.notes || ''}>
                      {r.divergence_reason || r.notes || 'Confluent alignment confirmed.'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
