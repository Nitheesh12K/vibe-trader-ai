import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { XGBoostResearchView } from './components/views/XGBoostResearchView';
import { api } from './services/api';

vi.mock('./services/api', () => ({
  api: {
    getXGBoostModels: vi.fn(),
    getXGBoostModelDetail: vi.fn(),
    trainXGBoost: vi.fn(),
    predictXGBoost: vi.fn(),
    getXGBoostPredictions: vi.fn(),
    synthesizeXGBoost: vi.fn(),
    getAIComparisonSummary: vi.fn(),
    evaluateAIComparison: vi.fn(),
  },
}));

const mockModelSummaries = [
  {
    model_id: 'xgb_test_model_123',
    experiment_id: 'exp_001',
    symbol: 'RELIANCE',
    timeframe: '1D',
    created_at: '2026-10-03T12:00:00Z',
    status: 'COMPLETED',
    test_accuracy: 0.655,
    test_f1: 0.642,
    test_roc_auc: 0.680,
    n_samples: 100,
  },
];

const mockModelDetail = {
  model_id: 'xgb_test_model_123',
  experiment_id: 'exp_001',
  symbol: 'RELIANCE',
  timeframe: '1D',
  created_at: '2026-10-03T12:00:00Z',
  hyperparameters: {
    n_estimators: 100,
    max_depth: 4,
    learning_rate: 0.05,
    early_stopping_rounds: 10,
    eval_metric: 'logloss',
    random_state: 42,
  },
  train_metrics: {
    accuracy: 0.75,
    precision: 0.74,
    recall: 0.76,
    f1: 0.75,
    roc_auc: 0.81,
    pr_auc: 0.79,
    balanced_accuracy: 0.75,
    log_loss: 0.52,
    brier_score: 0.18,
    confusion_matrix: [[30, 10], [10, 30]],
  },
  val_metrics: {
    accuracy: 0.68,
    precision: 0.67,
    recall: 0.70,
    f1: 0.68,
    roc_auc: 0.72,
    pr_auc: 0.70,
    balanced_accuracy: 0.68,
    log_loss: 0.59,
    brier_score: 0.21,
    confusion_matrix: [[7, 3], [3, 7]],
  },
  test_metrics: {
    accuracy: 0.655,
    precision: 0.64,
    recall: 0.66,
    f1: 0.642,
    roc_auc: 0.68,
    pr_auc: 0.66,
    balanced_accuracy: 0.65,
    log_loss: 0.62,
    brier_score: 0.23,
    confusion_matrix: [[6, 4], [3, 7]],
  },
  baseline_metrics: {
    majority_class: {
      predicted_class: 1,
      accuracy: 0.50,
      brier_score: 0.25,
    },
    momentum: {
      accuracy: 0.52,
      brier_score: 0.24,
    },
  },
  feature_importances: [
    { feature_name: 'rsi_14', gain: 0.24, weight: 15 },
    { feature_name: 'macd_hist_norm', gain: 0.18, weight: 12 },
    { feature_name: 'ema_spread_9_21', gain: 0.15, weight: 10 },
  ],
  walk_forward_results: [
    {
      fold: 1,
      train_start: '2024-01-01',
      train_end: '2024-06-01',
      test_start: '2024-06-02',
      test_end: '2024-07-01',
      train_samples: 50,
      test_samples: 10,
      test_accuracy: 0.60,
      test_f1: 0.58,
      test_roc_auc: 0.62,
      brier_score: 0.24,
    },
  ],
  dataset_info: {
    symbol: 'RELIANCE',
    timeframe: '1D',
    total_raw_bars: 100,
    usable_bars: 90,
    features_count: 9,
  },
  status: 'COMPLETED',
};

const mockPredictionHistory = [
  {
    id: 1,
    model_id: 'xgb_test_model_123',
    symbol: 'RELIANCE',
    prediction_timestamp: '2026-10-03T12:00:00Z',
    predicted_direction: 'BULLISH',
    probability_up: 0.68,
    confidence: 0.36,
    actual_direction: null,
    is_correct: null,
    created_at: '2026-10-03T12:00:00Z',
  },
];

describe('XGBoostResearchView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getXGBoostModels as any).mockResolvedValue(mockModelSummaries);
    (api.getXGBoostModelDetail as any).mockResolvedValue(mockModelDetail);
    (api.getXGBoostPredictions as any).mockResolvedValue(mockPredictionHistory);
    (api.getAIComparisonSummary as any).mockResolvedValue({
      total_records: 1,
      agreement_count: 1,
      divergence_count: 0,
      cautionary_count: 0,
      agreement_rate: 1.0,
      divergence_rate: 0.0,
      cautionary_rate: 0.0,
      records: [
        {
          record_id: 'CMP-001',
          timestamp: 1700000000,
          symbol: 'RELIANCE',
          market: 'NSE',
          timeframe: '1D',
          deterministic_strategy_name: 'STRAT-EMA-CROSS',
          deterministic_signal: 'BUY',
          deterministic_confidence: 0.8,
          xgboost_predicted_direction: 'UP',
          xgboost_probability: 0.78,
          qwen_synthesized_recommendation: 'BUY',
          concurrence_status: 'AGREE',
        },
      ],
    });
    (api.evaluateAIComparison as any).mockResolvedValue({
      record_id: 'CMP-NEW',
      concurrence_status: 'AGREE',
    });
  });

  it('renders research safety banner and non-negotiable notice', async () => {
    render(<XGBoostResearchView />);

    expect(screen.getByText(/XGBoost Quantitative Research Engine/i)).toBeInTheDocument();
    expect(screen.getByText(/RESEARCH ADVISORY ONLY — NOT A TRADE INSTRUCTION/i)).toBeInTheDocument();
    expect(screen.getByText(/NEVER execute orders directly/i)).toBeInTheDocument();

    await waitFor(() => expect(api.getXGBoostModels).toHaveBeenCalled());
  });

  it('displays out-of-sample test metrics and naive baselines for selected model', async () => {
    render(<XGBoostResearchView />);

    const modelItem = await screen.findByText(/RELIANCE/);
    expect(modelItem).toBeInTheDocument();
    fireEvent.click(modelItem);

    const accuracyText = await screen.findByText('Out-of-Sample Accuracy');
    expect(accuracyText).toBeInTheDocument();
    expect(screen.getAllByText('65.5%').length).toBeGreaterThan(0);
    expect(screen.getByText('Majority Class Baseline')).toBeInTheDocument();
    expect(screen.getByText('Momentum Direction Baseline')).toBeInTheDocument();
  });

  it('handles training workflow with parameter inputs', async () => {
    const mockTrainResponse = {
      success: true,
      model_id: 'xgb_new_trained_999',
      experiment_id: 'exp_002',
      symbol: 'RELIANCE',
      timeframe: '1D',
      metrics: {
        train: mockModelDetail.train_metrics,
        val: mockModelDetail.val_metrics,
        test: mockModelDetail.test_metrics,
      },
      feature_importances: mockModelDetail.feature_importances,
      walk_forward_results: mockModelDetail.walk_forward_results,
      baseline_metrics: mockModelDetail.baseline_metrics,
      message: 'Training completed',
    };
    (api.trainXGBoost as any).mockResolvedValue(mockTrainResponse);

    render(<XGBoostResearchView />);

    const trainButton = screen.getByRole('button', { name: /Run Training Pipeline/i });
    fireEvent.click(trainButton);

    await waitFor(() => {
      expect(api.trainXGBoost).toHaveBeenCalledWith(
        expect.objectContaining({
          symbol: 'RELIANCE',
          timeframe: '1D',
          random_state: 42,
        })
      );
    });
  });

  it('handles advisory next-bar prediction and shows probability meter', async () => {
    const mockPredictRes = {
      model_id: 'xgb_test_model_123',
      symbol: 'RELIANCE',
      prediction_timestamp: '2026-10-03T12:30:00Z',
      predicted_direction: 'BULLISH',
      probability_up: 0.72,
      probability_down: 0.28,
      confidence: 0.44,
      features_used: { rsi_14: 58.2, macd_hist_norm: 0.015 },
      top_contributing_features: [
        { feature_name: 'rsi_14', value: 58.2, contribution_score: 0.12 },
      ],
      rule_agreement: 'AGREES',
    };
    (api.predictXGBoost as any).mockResolvedValue(mockPredictRes);

    render(<XGBoostResearchView />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Forecast Next Bar/i })).not.toBeDisabled();
    });

    const forecastBtn = screen.getByRole('button', { name: /Forecast Next Bar/i });
    fireEvent.click(forecastBtn);

    await waitFor(() => {
      expect(api.predictXGBoost).toHaveBeenCalledWith({
        symbol: 'RELIANCE',
        timeframe: '1D',
        model_id: 'xgb_test_model_123',
      });
      expect(screen.getByText('Up: 72.0%')).toBeInTheDocument();
      expect(screen.getByText('Down: 28.0%')).toBeInTheDocument();
    });
  });

  it('handles Qwen advisory synthesis and warns on divergence', async () => {
    const mockSynthesizeRes = {
      symbol: 'RELIANCE',
      timestamp: '2026-10-03T12:35:00Z',
      rule_signal: 'BUY',
      xgboost_prediction: 'BEARISH',
      xgboost_confidence: 0.35,
      probability_up: 0.32,
      divergence_detected: true,
      divergence_warning: 'DIVERGENCE DETECTED: Rule-based strategy proposes BUY while XGBoost forecasts downward continuation.',
      unified_confidence: 0.45,
      synthesized_recommendation: 'CAUTION_BUY',
      qwen_advisory_text: 'Advisory analysis: While EMA indicates momentum, XGBoost flags high downside probability.',
      risk_disclaimer: 'Advisory only. Paper trading mode.',
    };
    (api.synthesizeXGBoost as any).mockResolvedValue(mockSynthesizeRes);

    render(<XGBoostResearchView />);

    const synthBtn = screen.getByRole('button', { name: /Synthesize Advisory/i });
    fireEvent.click(synthBtn);

    await waitFor(() => {
      expect(api.synthesizeXGBoost).toHaveBeenCalled();
      expect(screen.getByText(/Divergence Detected!/i)).toBeInTheDocument();
      expect(screen.getByText(/DIVERGENCE DETECTED: Rule-based strategy proposes BUY/i)).toBeInTheDocument();
      expect(screen.getByText(/CAUTION_BUY/i)).toBeInTheDocument();
    });
  });
});
