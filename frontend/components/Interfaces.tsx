export interface Clip {
  bullets: any;
  title: string;
  source: string;
  videoId: string;
  end: number;
  start: number;
  thumbnail: string;
  transcript: string;
}

export interface Subtopic {
  subtopic: string;
  clips: Clip[];
}

export interface Topic {
  topic: string;
  description: string;
  subtopics: Subtopic[];
}

export interface LiquidData {
  topics: Topic[];
}
export interface Random {
  _id: string;
  videoId: string;
  segmentIndex: number;
  url: string;
  topic: string;
}
