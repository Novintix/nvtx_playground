
import { Lead, LeadStage, LeadPriority } from './types';

export const MOCK_LEADS: Lead[] = [
  {
    id: '1',
    name: 'Robert Fox',
    title: 'CTO at CloudScale Dynamics',
    company: 'CloudScale Dynamics',
    email: 'robert.f@cloudscale.io',
    phone: '+1 (555) 234-8890',
    linkedin: 'linkedin.com/in/robertfox',
    industry: 'Cloud Infrastructure',
    employees: '250 - 500',
    revenue: '$50M - $100M',
    owner: 'Sarah Jenkins',
    ownerAvatar: 'https://picsum.photos/seed/sarah/100/100',
    source: 'Webinar 2024',
    created: 'Oct 12, 2024',
    priority: LeadPriority.HIGH,
    stage: LeadStage.PROPOSAL,
    estimatedValue: '$12,500',
    projectType: 'Cloud Services',
    activities: [
      {
        id: 'a1',
        type: 'call',
        title: 'Outgoing Call to Robert Fox',
        description: 'Discussed the proposal sent yesterday. Robert had some questions regarding the implementation timeline for Phase 2. He is generally satisfied with the pricing but needs to check with their CFO.',
        timestamp: '2 hours ago',
        loggedBy: 'Sarah Jenkins'
      },
      {
        id: 'a2',
        type: 'email',
        title: 'Proposal Sent: "Cloud Transformation 2024"',
        description: 'Automated System Email',
        timestamp: 'Oct 24, 11:30 AM',
        loggedBy: 'System',
        attachment: { name: 'proposal_v2_signed.pdf', size: '1.2 MB' }
      },
      {
        id: 'a3',
        type: 'meeting',
        title: 'Discovery Meeting',
        description: '"We need a partner that understands our hybrid-cloud complexities. Reliability is our #1 priority over cost at this stage." - Robert Fox',
        timestamp: 'Oct 22, 2:00 PM',
        loggedBy: 'Sarah Jenkins, Michael Chen'
      }
    ]
  },
  {
    id: '2',
    name: 'Jane Cooper',
    title: 'Director of Ops at Global Retail',
    company: 'Global Retail Inc',
    email: 'jane.c@globalretail.com',
    phone: '+1 (555) 987-6543',
    linkedin: 'linkedin.com/in/janecooper',
    industry: 'Retail',
    employees: '1000+',
    revenue: '$500M+',
    owner: 'Mark Weber',
    ownerAvatar: 'https://picsum.photos/seed/mark/100/100',
    source: 'Referral',
    created: 'Oct 14, 2024',
    priority: LeadPriority.MEDIUM,
    stage: LeadStage.DISCOVERY,
    estimatedValue: '$45,000',
    projectType: 'Development',
    activities: []
  },
  {
    id: '3',
    name: 'Albert Flores',
    title: 'CEO at TechCorp',
    company: 'TechCorp Solutions',
    email: 'albert@techcorp.com',
    phone: '+1 (555) 111-2222',
    linkedin: 'linkedin.com/in/albertflores',
    industry: 'Software',
    employees: '50 - 100',
    revenue: '$10M - $25M',
    owner: 'Sarah Jenkins',
    ownerAvatar: 'https://picsum.photos/seed/sarah/100/100',
    source: 'LinkedIn',
    created: 'Oct 12, 2024',
    priority: LeadPriority.HIGH,
    stage: LeadStage.DISCOVERY,
    estimatedValue: '$8,000',
    projectType: 'Cloud Services',
    activities: []
  }
];
