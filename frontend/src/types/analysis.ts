export interface AnalysisResponse {
  status: string
  authenticity_percentage: number
  risk_percentage: number
  risk_score: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | string
  reasons: string[]
  original_image_url: string
  heatmap_image_url: string
  extracted_fields: Record<string, string | number>
  anomaly_score: number
  authenticity_score: number
  inference_method: string
  component_scores: Record<string, number>
}
