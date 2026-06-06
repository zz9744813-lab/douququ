import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface Props {
  military: number;
  economy: number;
  defense: number;
  stability: number;
  territory: number;
  resources: number;
  width?: number;
  height?: number;
}

const DIMENSIONS = [
  { name: '战力', max: 100 },
  { name: '经济', max: 100 },
  { name: '防御', max: 100 },
  { name: '稳定', max: 100 },
  { name: '领土', max: 100 },
  { name: '资源', max: 100 },
];

export default function PowerRadarChart({
  military,
  economy,
  defense,
  stability,
  territory,
  resources,
  width = 280,
  height = 280,
}: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current);
    }
    const chart = instanceRef.current;

    const values = [military, economy, defense, stability, territory, resources];

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: '#12121e',
        borderColor: '#252540',
        textStyle: { color: '#e8e8ed', fontSize: 12 },
      },
      radar: {
        indicator: DIMENSIONS,
        shape: 'polygon',
        splitNumber: 4,
        axisName: {
          color: '#a0a0b4',
          fontSize: 11,
          fontFamily: "'Noto Sans SC', sans-serif",
        },
        splitArea: {
          areaStyle: {
            color: [
              'rgba(22, 184, 122, 0.02)',
              'rgba(22, 184, 122, 0.04)',
              'rgba(22, 184, 122, 0.06)',
              'rgba(22, 184, 122, 0.08)',
            ],
          },
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(22, 184, 122, 0.15)',
          },
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(22, 184, 122, 0.2)',
          },
        },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: values,
              name: '综合实力',
              symbol: 'circle',
              symbolSize: 4,
              lineStyle: {
                color: '#16b87a',
                width: 2,
              },
              itemStyle: {
                color: '#16b87a',
              },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(22, 184, 122, 0.35)' },
                  { offset: 1, color: 'rgba(22, 184, 122, 0.05)' },
                ]),
              },
            },
          ],
        },
      ],
    };

    chart.setOption(option, true);

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [military, economy, defense, stability, territory, resources]);

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