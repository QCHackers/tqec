// formattedInfoTab.js
const formattedInfoTabContent = (
  <div style={{textAlign: 'center', marginTop: '40px'}}>
    <p>Welcome to the TQEC app!</p>
    <p>We designed it to facilitate prototyping quantum error correcting codes.</p>
    <ul style={{ listStylePosition: 'inside', paddingLeft: '0' }}>
      <li style={{ paddingLeft: '116px', marginTop: '20px' }}>
        Select tab 'Compose library' to create a library of plaquette and addociate a circuit to each of them.<br />
        <span style={{ paddingLeft: '20px' }}>Each such plaquette represents a 'type' of stabilizer-measurement circuit available to the QEC code.</span>
      </li>
      <li style={{ paddingLeft: '0px', marginTop: '20px' }}>
        Select tab 'Create code' to stitch together the plaquettes and create the QEC code!
      </li>
    </ul>
  </div>
);

export default formattedInfoTabContent;
