const SettingsPage = () => {
  return (
    <div className="p-6 lg:p-10 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground">Configure your translation preferences</p>
      </div>

      <div className="space-y-6 max-w-2xl">
        <div className="rounded-lg border bg-card p-6 shadow-sm space-y-4">
          <h2 className="text-base font-semibold text-foreground">General</h2>
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Default Source Language</label>
              <select className="block w-full rounded-md border bg-background px-3 py-2 text-sm text-foreground">
                <option>English</option>
                <option>Japanese</option>
                <option>German</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Default Target Language</label>
              <select className="block w-full rounded-md border bg-background px-3 py-2 text-sm text-foreground">
                <option>Japanese</option>
                <option>German</option>
                <option>French</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Default Translation Mode</label>
              <select className="block w-full rounded-md border bg-background px-3 py-2 text-sm text-foreground">
                <option>High Accuracy</option>
                <option>Fast</option>
              </select>
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-card p-6 shadow-sm space-y-4">
          <h2 className="text-base font-semibold text-foreground">Notifications</h2>
          <label className="flex items-center gap-3 text-sm text-foreground">
            <input type="checkbox" defaultChecked className="accent-primary" />
            Email notifications for completed translations
          </label>
          <label className="flex items-center gap-3 text-sm text-foreground">
            <input type="checkbox" className="accent-primary" />
            Weekly usage summary
          </label>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
