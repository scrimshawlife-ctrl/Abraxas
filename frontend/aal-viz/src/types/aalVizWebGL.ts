export type DrawCallMode = 'LINES' | 'POINTS';

export interface AALVizWebGLRenderBundle {
  artifact: string;
  schema_version: string;
  buffers: { positions: number[]; colors: number[]; indices: number[] };
  draw_calls: Array<{ mode: DrawCallMode; count: number; offset: number }>;
  camera_uniforms: { position: [number, number, number]; target: [number, number, number]; zoom: number };
  material_uniforms: { color_palette: Record<string, string | number[] | unknown> };
  scene_summary: { node_count: number; edge_count: number };
}

export interface AALVizWebGLStaticViewerSpec {
  artifact: string;
  schema_version: string;
  viewer_id: string;
  draw_plan: { draw_calls: Array<{ mode: DrawCallMode; count: number; offset: number }>; node_draw_mode: 'POINTS'; edge_draw_mode: 'LINES' };
}

export interface AALVizCanaryWebGLStaticViewerProps {
  renderBundle: AALVizWebGLRenderBundle;
  viewerSpec: AALVizWebGLStaticViewerSpec;
  width: number;
  height: number;
  className?: string;
  debug?: boolean;
}
