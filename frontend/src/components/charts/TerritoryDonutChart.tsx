import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface DataItem {
  name: string;
  value: number;
  color?: string;
}

interface Props {
  data: DataItem[];
  width?: number;
  height?: number;
}

const DEFAULT_COLORS = [
  '#ef4444', '#16b87a', '#3b82f6', '#a855f7',
  '#f97316', '#eab308', '#14b8a6', '#6b7280',
  '#ec4899', '#06b6d4',
];

export default function TerritoryDonutChart({
  data,
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

    const seriesData = data.map((item, i) => ({
      name: item.name,
      value: item.value,
      itemStyle: {
        color: item.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length],
        borderRadius: 4,
      },
    }));

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: '#12121e',
        borderColor: '#252540',
        textStyle: { color: '#e8e8ed', fontSize: 12 },
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        show: false,
      },
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 4,
            borderColor: '#12121e',
            borderWidth: 2,
          },
          label: {
            show: true,
            color: '#a0a0b4',
            fontSize: 11,
            fontFamily: "'Noto Sans SC', sans-serif",
            formatter: '{b}',
          },
          labelLine: {
            lineStyle: {
              color: '#46466a',
            },
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 13,
              fontWeight: 'bold',
              color: '#e8e8ed',
            },
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
          data: seriesData,
        },
      ],
    };

    chart.setOption(option, true);

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data]);

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