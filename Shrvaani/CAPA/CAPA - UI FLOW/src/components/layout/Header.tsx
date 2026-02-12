import { Shield, Bell, User, SwitchCamera, ListChecks, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePersona, PersonaType, STAGES, PERSONA_CONFIGS } from "@/contexts/PersonaContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const Header = () => {
  const { persona, setPersona, config, allPersonas, stageIndex, setStageIndex } = usePersona();

  const visibleStagesInfos = STAGES.filter(s => config.visibleStages.includes(s.id));

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg gradient-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground">CAPA Manager</h1>
            <div className="flex items-center gap-2">
              <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">{config.name}</p>
              <Badge variant="outline" className="text-[8px] h-3 px-1 leading-none border-primary/30 text-primary uppercase">{config.role}</Badge>
            </div>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-6">
          <a href="/" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
            Home
          </a>
          <a href="/workflow" className="text-sm font-semibold text-primary hover:text-primary/80 transition-colors">
            Workflow App
          </a>
        </nav>

        <div className="flex items-center gap-2">
          {/* Stage Navigator (New Dropdown) */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-2 h-8 text-slate-600 hover:bg-slate-100">
                <ListChecks className="h-4 w-4" />
                <span className="hidden lg:inline text-xs font-semibold">Jump to Stage</span>
                <ChevronRight className="h-3 w-3 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64 p-2 shadow-2xl border-slate-100">
              <DropdownMenuLabel className="text-[10px] uppercase tracking-widest text-slate-400 py-2">Workflow Journey</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <div className="space-y-1 mt-1">
                {visibleStagesInfos.map((s, idx) => (
                  <DropdownMenuItem
                    key={s.id}
                    onClick={() => setStageIndex(idx)}
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${stageIndex === idx ? "bg-primary/10 text-primary font-bold" : "hover:bg-slate-50 text-slate-600"}`}
                  >
                    <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${stageIndex === idx ? s.color : 'bg-slate-100 text-slate-400'}`}>
                      <s.icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm leading-none">{s.label}</p>
                      <p className="text-[10px] text-muted-foreground mt-1 font-normal">{s.summary}</p>
                    </div>
                  </DropdownMenuItem>
                ))}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          <Separator orientation="vertical" className="h-6 mx-1" />

          {/* Persona Switcher */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2 h-8 border-slate-200">
                <SwitchCamera className="h-4 w-4" />
                <span className="hidden sm:inline">Switch Role</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>System Personas</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {allPersonas.map((p) => (
                <DropdownMenuItem
                  key={p}
                  onClick={() => setPersona(p)}
                  className={`flex flex-col items-start p-3 ${persona === p ? "bg-slate-100 font-bold" : ""}`}
                >
                  <span className="text-sm">{(allPersonas as any).includes(p) && (PERSONA_CONFIGS as any)[p].name}</span>
                  <span className="text-[10px] text-muted-foreground font-normal">{(PERSONA_CONFIGS as any)[p].role}</span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground h-8 w-8">
            <Bell className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground h-8 w-8">
            <User className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;
