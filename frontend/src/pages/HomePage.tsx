import { Layout } from '../components/layout/Layout';

export function HomePage() {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Welcome to LBG FTR Demo
        </h1>
        
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-gray-700 mb-4">
            This is a demonstration application for the LBG FTR (Faster Transaction Resolution) platform.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Accounts</h3>
              <p className="text-gray-600">
                View your account balances and recent transactions
              </p>
            </div>
            
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Payments</h3>
              <p className="text-gray-600">
                Make payments to saved payees or add new recipients
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
