
import { GoogleGenAI } from "@google/genai";
import { Lead } from "./types";

export const getLeadAISummary = async (lead: Lead): Promise<string> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
  
  const activityLogs = lead.activities.map(a => `- ${a.title}: ${a.description}`).join('\n');
  
  const prompt = `
    Analyze the following CRM lead and their activity history. 
    Provide a concise (2-3 sentence) summary of the current status and suggest the single most effective "Next Best Action" to move this deal forward.
    
    Lead Name: ${lead.name}
    Company: ${lead.company}
    Stage: ${lead.stage}
    Priority: ${lead.priority}
    
    Activities:
    ${activityLogs}
    
    Format the response as:
    Summary: [Summary text]
    Next Best Action: [Action text]
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
    });
    return response.text || "Unable to generate summary at this time.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Error connecting to AI service.";
  }
};
