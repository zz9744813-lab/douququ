import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface Props {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
}

export default function Sparkline({
  data,
  color = '#16b87a',
  width = 120,
  height = 32,
}: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current);
    }
    const chart = instanceRef.current;

    const option: echarts.EChartsOption = {
      animation: false,
      grid: {
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
      },
      xAxis: {
        type: 'category',
        show: false,
        data: data.map((_, i) => i),
      },
      yAxis: {
        type: 'value',
        show: false,
        min: (value: { min: number }) => Math.floor(value.min * 0.9),
        max: (value: { max: number }) => Math.ceil(value.max * 1.1),
      },
      series: [
        {
          type: 'line',
          data,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 1.5,
            color,
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: color + '40' },
              { offset: 1, color: color + '05' },
            ]),
          },
        },
      ],
    };

    chart.setOption(option, true);

    return () => {
      // 不在每次更新时销毁，只在组件卸载时销毁
    };
  }, [data, color]);

  useEffect(() => {
    return () => {
      instanceRef.current?.dispose();
      instanceRef.current = null;
    };
  }, []);

  return (
    <div
      ref={chartRef}
      style={{ width: `${width}px`, height: `${height}px` }}
    />
  );
}