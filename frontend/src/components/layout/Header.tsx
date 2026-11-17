import { useAuth } from '../../lib/auth-context';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-surface border-b border-line px-s4 py-s3 flex items-center justify-between">
      <div className="flex items-center gap-s3">
        <h1 className="font-head text-xl font-bold text-ink">Clear Path</h1>
      </div>
      
      <div className="flex items-center gap-s4">
        {user && (
          <>
            <span className="text-sm text-muted">{user.email}</span>
            <button
              onClick={() => logout()}
              className="px-s3 py-s2 text-sm font-semibold text-primary hover:bg-primary-soft rounded-field transition-colors"
            >
              Sign out
            </button>
          </>
        )}
      </div>
    </header>
  );
}
