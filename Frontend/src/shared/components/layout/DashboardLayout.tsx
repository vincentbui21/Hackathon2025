import { Outlet } from 'react-router-dom';
import { SidebarProvider, SidebarInset } from '@/shared/components/ui/sidebar';
import { AppSidebar } from './AppSidebar';

export function DashboardLayout() {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full bg-gray-50/50">
        <AppSidebar />
        <SidebarInset className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-7xl mx-auto p-6 md:p-8">
              <Outlet />
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
