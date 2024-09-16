import { useEffect, useContext, useState, React } from "react";
import PropTypes from "prop-types";
import { UserContext } from "./UserContext";

export default function SecuritySearch({refresh = () => {}}) {
  const { user } = useContext(UserContext);
  const [search, setSearch] = useState('');
  const [foundTickers, setFoundTickers] = useState({});
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!user || !user?.token || !search) return;

    // TODO - kill previous calls
    fetch(`http://localhost:8000/security/search?ticker=${search}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${user?.token}`,
        },
      },
    )
    .then(response => response.json())
    .then(data => {
      if (data?.error) {
        setFoundTickers({});
        setErrorMessage(data.error);
        return;
      }

      const tickers = data?.tickers || {};
      setFoundTickers(tickers);
      setErrorMessage("");
    });
  }, [user, search]);

  function addTickerToPortfolio(ticker) {
    fetch(`http://localhost:8000/security/add`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${user.token}`,
        },
        body: JSON.stringify({ticker}),
      },
    )
    .then(() => {
      setSearch("");
      setFoundTickers({});
      refresh();
    });
  }

  return (
    <>
      <input type="text" value={search} placeholder="Enter a ticker symbol" onChange={(event) => setSearch(event?.target?.value?.toUpperCase())} />
      <i className="fa fa-search" style={{marginLeft: "6px", marginRight: "6px"}}></i>
      {errorMessage && <span style={{color: "red"}}>{errorMessage}</span>}

      <div style={{margin: "6px"}}>
        {Object.keys(foundTickers).map(ticker => {
          return (
            <div key={ticker} style={{cursor: "pointer"}} onClick={() => addTickerToPortfolio(ticker)}>
              <span>{ticker}</span>
              <i className="fa fa-plus" style={{marginLeft: "6px"}}></i>
            </div>
          );
        })}
      </div>
    </>
  );
}

SecuritySearch.propTypes = {
  refresh: PropTypes.func,
};
