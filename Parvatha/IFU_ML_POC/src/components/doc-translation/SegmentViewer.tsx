import type { Segment, TranslatedSegment } from "@/lib/api";

interface SegmentViewerProps {
  segments: Segment[];
  translations?: TranslatedSegment[];
}

export function SegmentViewer({ segments, translations }: SegmentViewerProps) {
  const getTranslatedText = (id: number) =>
    translations?.find((t) => t.id === id)?.translated_text;

  return (
    <div className="space-y-1">
      {segments.map((seg) => {
        const text = translations ? getTranslatedText(seg.id) ?? seg.text : seg.text;
        return <SegmentBlock key={seg.id} type={seg.type} text={text} />;
      })}
    </div>
  );
}

function SegmentBlock({ type, text }: { type: Segment["type"]; text: string }) {
  switch (type) {
    case "h1":
      return <h1 className="text-xl font-bold text-foreground mt-6 mb-2">{text}</h1>;
    case "h2":
      return <h2 className="text-lg font-semibold text-foreground mt-5 mb-1.5">{text}</h2>;
    case "h3":
      return <h3 className="text-base font-semibold text-foreground mt-4 mb-1">{text}</h3>;
    case "li":
      return (
        <div className="flex gap-2 ml-4">
          <span className="text-muted-foreground mt-0.5">•</span>
          <p className="text-sm text-foreground leading-relaxed">{text}</p>
        </div>
      );
    case "ol":
      return (
        <div className="flex gap-2 ml-4">
          <p className="text-sm text-foreground leading-relaxed">{text}</p>
        </div>
      );
    case "p":
    default:
      return <p className="text-sm text-foreground leading-relaxed">{text}</p>;
  }
}
