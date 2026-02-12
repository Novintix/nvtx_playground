import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import HeroSection from "@/components/sections/HeroSection";
import WorkflowSection from "@/components/sections/WorkflowSection";
import StatsSection from "@/components/sections/StatsSection";
import PagesSection from "@/components/sections/PagesSection";
import AgentsSection from "@/components/sections/AgentsSection";
import RolesSection from "@/components/sections/RolesSection";

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <HeroSection />
        <StatsSection />
        <WorkflowSection />
        <PagesSection />
        <AgentsSection />
        <RolesSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
