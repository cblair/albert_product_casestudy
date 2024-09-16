import { useState, useCallback, useMemo } from 'react';
import Cookies from 'js-cookie';
import './App.css';
import { LoginForm } from './LoginForm';
import { UserContext } from './UserContext';
import { User } from "./User.jsx";
import { Securities } from "./Securities.jsx";

function App() {
  let userCookie = null;
  try {
    userCookie = JSON.parse(Cookies.get('user'));
  } catch (e) {}
  const [user, setUser] = useState(userCookie);
  const login = useCallback((u) => {
    Cookies.set('user', JSON.stringify(u), { expires: 7, secure: true });
    setUser(u);
  }, []);
  const logout = useCallback(() => {
    Cookies.remove('user');
    setUser(null);
  }, []);
  const value = useMemo(() => ({ user, login, logout }), [user, login, logout]);

  return (
    <UserContext.Provider value={value}>
      <div className="app">
        <LoginForm />
        <header>
          <h1>Albert stock watch</h1>
          <User />
        </header>
        {user && (
          <Securities />
        )}
      </div>
    </UserContext.Provider>
  );
}

export default App;
