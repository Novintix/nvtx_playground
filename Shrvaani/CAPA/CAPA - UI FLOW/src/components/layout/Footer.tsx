import { Shield } from "lucide-react";

const Footer = () => {
  return (
    <footer className="border-t border-border bg-card py-12">
      <div className="container">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary">
              <Shield className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-medium text-foreground">CAPA Manager</span>
          </div>
          
          <p className="text-sm text-muted-foreground">
            © 2025 Quality Management System. Ensuring compliance and continuous improvement.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
