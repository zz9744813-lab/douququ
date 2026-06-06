import { useState, useEffect, useRef } from 'react';
import { Skull } from 'lucide-react';
import type { Sect } from '../../api/client';

interface Props {
  sects: Sect[];
  previousSectIds?: string[];
}

export default function EliminationEffect({ sects, previousSectIds = [] }: Props) {
  const [eliminated, setEliminated] = useState<string | null>(null);
  const [show, setShow] = useState(false);
  const prevIdsRef = useRef<Set<string>>(new Set(previousSectIds));

  useEffect(() => {
    const currentIds = new Set(sects.map((s) => s.id));
    const prevIds = prevIdsRef.current;

    // 找出被吞并的宗门（之前存在但现在不存在，且状态不是新建的）
    const annexed: string[] = [];
    prevIds.forEach((id) => {
      if (!currentIds.has(id)) {
        annexed.push(id);
      }
    });

    if (annexed.length > 0) {
      // 显示最后一个被吞并的宗门
      setEliminated(annexed[annexed.length - 1]);
      setShow(true);

      const timer = setTimeout(() => {
        setShow(false);
      }, 3000);

      return () => clearTimeout(timer);
    }

    // 更新引用
    prevIdsRef.current = currentIds;
  }, [sects]);

  useEffect(() => {
    if (previousSectIds.length > 0) {
      prevIdsRef.current = new Set(previousSectIds);
    }
  }, [previousSectIds]);

  // 从之前的宗门列表中查找被吞并宗门的名称
  const eliminatedName = eliminated
    ? [...prevIdsRef.current].reduce<string | null>((name, id) => {
        if (id === eliminated) {
          // 尝试从所有已知宗门中查找
          return null; // ID 已不在 sects 中，需要从外部获取名称
        }
        return name;
      }, null) ?? eliminated
    : null;

  if (!show || !eliminated) return null;

  return (
    <div className="fixed inset-0 z-[60] pointer-events-none flex items-center justify-center">
      <div className="animate-elimination absolute inset-0" />
      <div className="relative z-10 flex flex-col items-center gap-3">
        <Skull className="w-16 h-16 text-vermilion-500" />
        <div className="text-center">
          <div className="text-vermilion-400 text-sm font-sans tracking-widest mb-1">
            宗门覆灭
          </div>
          <div className="text-vermilion-300 text-2xl font-serif font-bold">
            {eliminatedName}
          </div>
        </div>
      </div>
    </div>
  );
}