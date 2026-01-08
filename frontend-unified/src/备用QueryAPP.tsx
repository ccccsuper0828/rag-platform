import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Proposals from "./pages/Proposals";
import CreateProposal from "./pages/CreateProposal";
import ProposalDetail from "./pages/ProposalDetail";
import Analytics from "./pages/Analytics";
import Header from "./components/Header";

const queryClient = new QueryClient();

const App = () => {
  console.log('DAO Governance Platform initialized');
  
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background">
          <Header />
          <main className="w-full max-w-[1440px] mx-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/proposals" element={<Proposals />} />
              <Route path="/create-proposal" element={<CreateProposal />} />
              <Route path="/proposal" element={<ProposalDetail />} />
              <Route path="/analytics" element={<Analytics />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;