import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface Props {
  sectNames: string[];
  matrix: number[][];
  width?: number;
  height?: number;
}

export default function DiplomacyHeatmap({
  sectNames,
  matrix,
  width = 400,
  height = 400,
}: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || !sectNames.length || !matrix.length) return;

    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current);
    }
    const chart = instanceRef.current;

    // 构建 heatmap 数据: [x, y, value]
    const heatData: Array<[number, number, number]> = [];
    matrix.forEach((row, y) => {
      row.forEach((val, x) => {
        heatData.push([x, y, val]);
      });
    });

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        position: 'top',
        backgroundColor: '#12121e',
        borderColor: '#252540',
        textStyle: { color: '#e8e8ed', fontSize: 12 },
        formatter: (params: unknown) => {
          const p = params as { data: [number, number, number] };
          const [x, y, val] = p.data;
          const nameA = sectNames[x] || '';
          const nameB = sectNames[y] || '';
          const relation = val > 30 ? '友好' : val < -30 ? '敌对' : '中立';
          return `<strong>${nameA}</strong> → <strong>${nameB}</strong><br/>` +
            `关系值: ${val}<br/>态度: ${relation}`;
        },
      },
      grid: {
        left: 80,
        right: 40,
        top: 20,
        bottom: 60,
      },
      xAxis: {
        type: 'category',
        data: sectNames,
        splitArea: { show: false },
        axisLabel: {
          color: '#a0a0b4',
          fontSize: 10,
          fontFamily: "'Noto Sans SC', sans-serif",
          rotate: 45,
        },
        axisLine: { lineStyle: { color: '#36365a' } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'category',
        data: sectNames,
        splitArea: { show: false },
        axisLabel: {
          color: '#a0a0b4',
          fontSize: 10,
          fontFamily: "'Noto Sans SC', sans-serif",
        },
        axisLine: { lineStyle: { color: '#36365a' } },
        axisTick: { show: false },
      },
      visualMap: {
        min: -100,
        max: 100,
        calculable: false,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        itemWidth: 12,
        itemHeight: 120,
        textStyle: {
          color: '#787894',
          fontSize: 10,
        },
        inRange: {
          color: [
            '#ef4444', // -100 敌对 (红)
            '#7f1d1d',
            '#46466a', // 0 中立 (灰)
            '#0c4d39',
            '#16b87a', // 100 友好 (绿)
          ],
        },
      },
      series: [
        {
          type: 'heatmap',
          data: heatData,
          label: {
            show: false,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
              borderColor: '#e8e8ed',
              borderWidth: 1,
            },
          },
          itemStyle: {
            borderColor: '#12121e',
            borderWidth: 2,
            borderRadius: 2,
          },
        },
      ],
    };

    chart.setOption(option, true);

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [sectNames, matrix]);

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