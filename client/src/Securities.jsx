import { useContext, useEffect, useState, React } from "react";
import SecuritySearch from "./SecuritySearch";
import { UserContext } from "./UserContext";

const REFRESH_INTERVAL = 5000;

export function Securities() {
  const [securities, setSecurities] = useState({});
  const [securityToRemove, setSecurityToRemove] = useState(null);
  const [loading, setLoading] = useState(true);
  const {user} = useContext(UserContext);

  const removeSecurity = () => {
    fetch(`http://localhost:8000/security/remove`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${user?.token}`,
        },
        body: JSON.stringify({ticker: securityToRemove}),
      }
    )
    .then(() => setSecurityToRemove(null))
    .then(() => getSecurities());
  };

  const getSecurities = () => {
    if (!user || !user?.token) return;

    return fetch("http://localhost:8000/security/all",
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application',
          'Authorization': `Token ${user?.token}`,
        }
      }
    )
    .then(response => response.json())
    .then(data => setSecurities(data))
    .then(() => setLoading(false))
    .catch(() => {
      setSecurities({});
      setLoading(false);
    });
  };

  useEffect(() => {
    if (!user || !user?.token) return;

    // TODO - kill previous calls
    getSecurities();
    const interval = setInterval(getSecurities, REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [user]);

  function numberFormattedToDollarString(number) {
    return number?.toLocaleString('en-US', {style: 'currency', currency: 'USD'});
  }

  const securityEntries = Object.entries(securities);

  return (
    <div className='securities'>
      <h1>Securities</h1>

      <SecuritySearch refresh={getSecurities} />

      <hr />

      <table>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Price</th>
            <th>
            {loading ? 
              <i className="fa fa-spin fa-refresh"/>
              :
              <i className="fa fa-refresh"/>
            }
            </th>
          </tr>
        </thead>

        <tbody>
          {securityEntries.map(([ticker, price]) => {
            return (
              <tr key={ticker}>
                <td style={{minWidth: "60px"}}>{ticker}</td>
                <td style={{minWidth: "70px", textAlign: "right"}}>{price ? numberFormattedToDollarString(price) : "-"}</td>
                <td style={{minWidth: "120px", textAlign: "center"}}>
                  {securityToRemove === ticker ? 
                    <span className="security-trash"><button onClick={removeSecurity}>Are you sure?</button> <span style={{color: "red"}} onClick={() => setSecurityToRemove(null)}>X</span></span>
                    :
                    <i id={ticker} className="fa fa-trash security-trash" onClick={event => setSecurityToRemove(event?.target?.id)}></i>
                  }
                </td>
              </tr>
            );
          })
        }
        </tbody>
      </table>
    </div>
  );
}
