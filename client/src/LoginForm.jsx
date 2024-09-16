import { useCallback, useContext, useState } from 'react';
import { UserContext } from './UserContext';

export function LoginForm() {
  // Get login function from user context.
  const { user, login } = useContext(UserContext);

  // Form control.
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  // Make call to backend server to login. Save user object to user context.
  const handleLogin = useCallback((event) => {
    event.preventDefault();
    fetch('http://localhost:8000/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    .then((response) => response.json())
    .then((data) => {
      if (!data.token) {
        console.error('Unable to login', data);
        throw new Error(JSON.stringify(data));
      }

      login(data);
      console.info('Logged in successfully');
    })
    .catch((error) => {
      console.error('Unable to login', error);
      setError("Login failed, invalid username or password. Please try again.");
    });
  }, [username, password]);

  if (user) return null;

  return (
    <div className='login-form'>
      <form onSubmit={ handleLogin }>
        <h2>Log in</h2>
        <div className="inputs">
          <input
            type="text"
            id="username"
            placeholder="Enter your username"
            value={ username }
            onChange={ (event) => {
              setUsername(event.target.value);
              setError('');
            } }
          />
          <input
            type="password"
            id="password"
            placeholder="Enter your password"
            value={ password }
            onChange={ (event) => {
              setPassword(event.target.value);
              setError('');
            } }
          />
          <button type="submit">Login</button>
          { error && <p className="login-error">{ error }</p> }
        </div>
      </form>
    </div>
  );
}
