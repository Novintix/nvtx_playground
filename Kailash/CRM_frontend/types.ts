
export enum LeadStage {
  DISCOVERY = 'Discovery',
  PROPOSAL = 'Proposal',
  NEGOTIATION = 'Negotiation',
  CLOSED = 'Closed'
}

export enum LeadPriority {
  HIGH = 'High',
  MEDIUM = 'Medium',
  LOW = 'Low'
}

export type ActivityType = 'call' | 'email' | 'meeting' | 'task';

export interface Activity {
  id: string;
  type: ActivityType;
  title: string;
  description: string;
  timestamp: string;
  loggedBy: string;
  attachment?: {
    name: string;
    size: string;
  };
}

export interface Lead {
  id: string;
  name: string;
  title: string;
  company: string;
  email: string;
  phone: string;
  linkedin: string;
  industry: string;
  employees: string;
  revenue: string;
  owner: string;
  ownerAvatar: string;
  source: string;
  created: string;
  priority: LeadPriority;
  stage: LeadStage;
  estimatedValue: string;
  projectType: string;
  activities: Activity[];
}
