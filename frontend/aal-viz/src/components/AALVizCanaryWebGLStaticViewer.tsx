import React, { useEffect, useMemo, useRef, useState } from 'react';
import type { AALVizCanaryWebGLStaticViewerProps } from '../types/aalVizWebGL';

const VERTEX_SHADER = `
attribute vec3 position;
attribute vec3 color;
varying vec3 vColor;
void main() {
  vColor = color;
  gl_PointSize = 8.0;
  gl_Position = vec4(position.x / 600.0, position.y / 400.0, 0.0, 1.0);
}
`;

const FRAGMENT_SHADER = `
precision mediump float;
varying vec3 vColor;
void main() {
  gl_FragColor = vec4(vColor, 1.0);
}
`;

export const AALVizCanaryWebGLStaticViewer: React.FC<AALVizCanaryWebGLStaticViewerProps> = ({
  renderBundle,
  viewerSpec,
  width,
  height,
  className,
  debug = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [webglReady, setWebglReady] = useState(true);

  const debugSummary = useMemo(() => ({
    viewer_id: viewerSpec.viewer_id,
    node_count: renderBundle.scene_summary?.node_count ?? 0,
    edge_count: renderBundle.scene_summary?.edge_count ?? 0,
    positions_length: renderBundle.buffers?.positions?.length ?? 0,
    colors_length: renderBundle.buffers?.colors?.length ?? 0,
    indices_length: renderBundle.buffers?.indices?.length ?? 0,
  }), [viewerSpec.viewer_id, renderBundle]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const gl = canvas.getContext('webgl');
    if (!gl) {
      setWebglReady(false);
      return;
    }
    setWebglReady(true);

    const compileShader = (type: number, source: string): WebGLShader | null => {
      const shader = gl.createShader(type);
      if (!shader) return null;
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) return null;
      return shader;
    };

    const vertexShader = compileShader(gl.VERTEX_SHADER, VERTEX_SHADER);
    const fragmentShader = compileShader(gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
    if (!vertexShader || !fragmentShader) {
      setWebglReady(false);
      return;
    }

    const program = gl.createProgram();
    if (!program) {
      setWebglReady(false);
      return;
    }
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      setWebglReady(false);
      return;
    }
    gl.useProgram(program);

    const positions = new Float32Array(renderBundle.buffers?.positions ?? []);
    const colors = new Float32Array(renderBundle.buffers?.colors ?? []);
    const indices = new Uint16Array(renderBundle.buffers?.indices ?? []);

    const positionBuffer = gl.createBuffer();
    const colorBuffer = gl.createBuffer();
    const indexBuffer = gl.createBuffer();
    if (!positionBuffer || !colorBuffer || !indexBuffer) return;

    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
    const positionLoc = gl.getAttribLocation(program, 'position');
    if (positionLoc >= 0) {
      gl.enableVertexAttribArray(positionLoc);
      gl.vertexAttribPointer(positionLoc, 3, gl.FLOAT, false, 0, 0);
    }

    gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, colors, gl.STATIC_DRAW);
    const colorLoc = gl.getAttribLocation(program, 'color');
    if (colorLoc >= 0) {
      gl.enableVertexAttribArray(colorLoc);
      gl.vertexAttribPointer(colorLoc, 3, gl.FLOAT, false, 0, 0);
    }

    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);

    gl.viewport(0, 0, width, height);
    gl.clearColor(0.01, 0.02, 0.05, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    const drawCalls = viewerSpec.draw_plan?.draw_calls ?? renderBundle.draw_calls ?? [];
    drawCalls.forEach((call) => {
      if (call.mode === 'POINTS') {
        gl.drawArrays(gl.POINTS, call.offset, call.count);
      } else if (call.mode === 'LINES') {
        gl.drawElements(gl.LINES, call.count, gl.UNSIGNED_SHORT, call.offset * 2);
      }
    });
  }, [renderBundle, viewerSpec, width, height]);

  return (
    <div className={className}>
      {!webglReady && <div>WebGL not supported</div>}
      <canvas ref={canvasRef} width={width} height={height} />
      {debug ? <pre>{JSON.stringify(debugSummary, null, 2)}</pre> : null}
    </div>
  );
};

export default AALVizCanaryWebGLStaticViewer;
