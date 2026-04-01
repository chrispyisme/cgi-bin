const { useState, useEffect, useMemo } = React;

function InvoiceApp() {
    // Persistent State
    const [invoices, setInvoices] = useState(() => JSON.parse(localStorage.getItem('inv_data')) || []);
    const [contractors, setContractors] = useState(() => JSON.parse(localStorage.getItem('inv_contractors')) || ["General Vendor"]);
    const [owners, setOwners] = useState(() => JSON.parse(localStorage.getItem('inv_owners')) || ["Main Office"]);

    // UI State
    const [search, setSearch] = useState('');
    const [newEntry, setNewEntry] = useState('');
    const [formData, setFormData] = useState({
        owner: '', contractor: '', invNum: '', checkNum: '', amount: '', invDate: '', checkDate: ''
    });

    // Sync to LocalStorage
    useEffect(() => { localStorage.setItem('inv_data', JSON.stringify(invoices)); }, [invoices]);
    useEffect(() => { localStorage.setItem('inv_contractors', JSON.stringify(contractors)); }, [contractors]);
    useEffect(() => { localStorage.setItem('inv_owners', JSON.stringify(owners)); }, [owners]);

    // Relational Logic: Add to Master Lists
    const addToList = (type) => {
        if (!newEntry) return;
        if (type === 'contractor') setContractors([...new Set([...contractors, newEntry])]);
        else setOwners([...new Set([...owners, newEntry])]);
        setNewEntry('');
    };

    const removeFromList = (type, val) => {
        if (type === 'contractor') setContractors(contractors.filter(c => c !== val));
        else setOwners(owners.filter(o => o !== val));
    };

    // Calculate Totals per Contractor
    const stats = useMemo(() => {
        return invoices.reduce((acc, inv) => {
            acc[inv.contractor] = (acc[inv.contractor] || 0) + parseFloat(inv.amount || 0);
            return acc;
        }, {});
    }, [invoices]);

    const handleSubmit = (e) => {
        e.preventDefault();
        setInvoices([{ ...formData, id: Date.now() }, ...invoices]);
        setFormData({ ...formData, invNum: '', checkNum: '', amount: '', invDate: '', checkDate: '' });
    };

    const exportCSV = () => {
        const headers = "Owner,Contractor,Invoice#,Check#,Amount,Date\n";
        const rows = invoices.map(i => `${i.owner},${i.contractor},${i.invNum},${i.checkNum},${i.amount},${i.invDate}`).join("\n");
        const blob = new Blob([headers + rows], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'invoice_report.csv';
        a.click();
    };

    const filtered = invoices.filter(i => 
        i.contractor.toLowerCase().includes(search.toLowerCase()) || 
        i.owner.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="container">
            <div className="header-flex">
                <h1>Invoice System <span style={{color:'var(--accent)'}}>v3.0</span></h1>
                <button onClick={exportCSV} className="export-btn">💾 Export CSV</button>
            </div>

            {/* List Management Section */}
            <div className="settings-panel">
                <div className="list-manager">
                    <h3>Manage Owners & Contractors</h3>
                    <div style={{display:'flex', gap:'5px', marginBottom:'10px'}}>
                        <input value={newEntry} onChange={e => setNewEntry(e.target.value)} placeholder="Name..." />
                        <button onClick={() => addToList('owner')} style={{background:'var(--accent)', border:'none', borderRadius:'4px', padding:'0 10px'}}>+ Owner</button>
                        <button onClick={() => addToList('contractor')} style={{background:'var(--success)', border:'none', borderRadius:'4px', padding:'0 10px'}}>+ Contractor</button>
                    </div>
                    <div className="chip-container">
                        {owners.map(o => <span key={o} className="chip" style={{borderLeft:'3px solid var(--accent)'}}>{o} <button onClick={() => removeFromList('owner', o)}>×</button></span>)}
                        {contractors.map(c => <span key={c} className="chip" style={{borderLeft:'3px solid var(--success)'}}>{c} <button onClick={() => removeFromList('contractor', c)}>×</button></span>)}
                    </div>
                </div>
                
                <div className="list-manager">
                    <h3>Quick Stats</h3>
                    <div style={{maxHeight:'100px', overflowY:'auto'}}>
                        {Object.entries(stats).map(([name, total]) => (
                            <div key={name} style={{display:'flex', justifyContent:'space-between', fontSize:'0.8rem', borderBottom:'1px solid #334155'}}>
                                <span>{name}</span>
                                <span style={{color:'var(--success)'}}>${total.toFixed(2)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Entry Form */}
            <form onSubmit={handleSubmit}>
                <div className="form-grid">
                    <select value={formData.owner} onChange={e => setFormData({...formData, owner: e.target.value})} required>
                        <option value="">Select Owner</option>
                        {owners.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                    <select value={formData.contractor} onChange={e => setFormData({...formData, contractor: e.target.value})} required>
                        <option value="">Select Contractor</option>
                        {contractors.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                    <input placeholder="Invoice #" value={formData.invNum} onChange={e => setFormData({...formData, invNum: e.target.value})} required />
                    <input placeholder="Check #" value={formData.checkNum} onChange={e => setFormData({...formData, checkNum: e.target.value})} />
                    <input type="number" step="0.01" placeholder="Amount" value={formData.amount} onChange={e => setFormData({...formData, amount: e.target.value})} required />
                    <input type="date" value={formData.invDate} onChange={e => setFormData({...formData, invDate: e.target.value})} />
                </div>
                <button type="submit" className="add-btn">Record Payment</button>
            </form>

            <input className="search-bar" placeholder="Filter by Owner or Contractor..." onChange={e => setSearch(e.target.value)} />

            <table>
                <thead>
                    <tr>
                        <th>Owner / Contractor</th>
                        <th>Invoice #</th>
                        <th>Check #</th>
                        <th>Amount</th>
                        <th>Date</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {filtered.map(i => (
                        <tr key={i.id}>
                            <td>
                                <span className="owner-tag">{i.owner}</span>
                                <strong>{i.contractor}</strong>
                            </td>
                            <td>{i.invNum}</td>
                            <td>{i.checkNum}</td>
                            <td style={{color:'var(--success)'}}>${parseFloat(i.amount).toFixed(2)}</td>
                            <td>{i.invDate}</td>
                            <td><button onClick={() => setInvoices(invoices.filter(x => x.id !== i.id))} className="delete-btn">🗑️</button></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<InvoiceApp />);