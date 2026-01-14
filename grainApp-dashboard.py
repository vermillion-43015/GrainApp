import json

def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grain Title Tracking Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #3a3a3a 0%, #4d4d4d 50%, #606060 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .header { background: linear-gradient(135deg, #3d6ba8 0%, #2c5282 100%); color: white; padding: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .user-info { margin-top: 10px; background: rgba(255,255,255,0.15); padding: 15px; border-radius: 8px; }
        .nav-buttons { display: flex; gap: 10px; padding: 20px; background: #f8f9fa; flex-wrap: wrap; }
        .nav-btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 1em; font-weight: 600; transition: all 0.3s; }
        .nav-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: #000; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-purple { background: #6f42c1; color: white; }
        .content { padding: 30px; min-height: 400px; }
        .loading { text-align: center; padding: 50px; font-size: 1.2em; color: #666; }
        .item-card { background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 10px; padding: 20px; margin-bottom: 15px; transition: all 0.3s; }
        .item-card:hover { background: #e9ecef; border-color: #2c5282; box-shadow: 0 4px 12px rgba(44,82,130,0.3); }
        .item-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; }
        .item-header h3 { color: #2c5282; font-size: 1.1em; margin: 0; }
        .item-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .detail-row { display: flex; flex-direction: column; }
        .detail-label { font-size: 0.85em; color: #666; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
        .detail-value { font-size: 1.1em; font-weight: 600; color: #333; }
        .grain-badge { display: inline-block; padding: 5px 15px; border-radius: 15px; font-weight: 600; font-size: 0.9em; }
        .grain-corn { background: #fff3cd; color: #856404; }
        .grain-wheat { background: #f8d7da; color: #721c24; }
        .grain-soybean { background: #d4edda; color: #155724; }
        .grain-oats { background: #d1ecf1; color: #0c5460; }
        .validation-status { padding: 5px 12px; border-radius: 12px; font-weight: 600; font-size: 0.85em; }
        .status-valid { background: #d4edda; color: #155724; }
        .status-invalid { background: #f8d7da; color: #721c24; }
        .status-checking { background: #fff3cd; color: #856404; }
        .form-container { background: #fff; border-radius: 10px; padding: 30px; max-width: 800px; margin: 0 auto; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        .form-group input, .form-group select { width: 100%; padding: 12px; border: 2px solid #dee2e6; border-radius: 8px; font-size: 1em; }
        .form-group input:focus, .form-group select:focus { outline: none; border-color: #2c5282; }
        .form-actions { display: flex; gap: 10px; margin-top: 30px; }
        .alert { padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .hash-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border: 2px solid #dee2e6; }
        .hash-label { font-weight: 600; color: #2c5282; margin-bottom: 5px; }
        .hash-value { font-family: monospace; word-break: break-all; color: #495057; font-size: 0.9em; }
        .hash-clickable { cursor: pointer; transition: all 0.3s; }
        .hash-clickable:hover { background: #e9ecef; border-color: #2c5282; }
        .hash-hint { font-size: 0.85em; color: #666; font-style: italic; margin-top: 5px; }
        .price-hint { font-size: 0.85em; color: #666; margin-top: 5px; }
        .action-btn { padding: 10px 25px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.3s; margin-right: 10px; }
        .action-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .action-btn:disabled { background: #6c757d; cursor: not-allowed; transform: none; }
        .buy-btn { background: #28a745; color: white; }
        .relist-btn { background: #17a2b8; color: white; }
        .user-indicator { background: #e7f3ff; border: 2px solid #007bff; padding: 12px 15px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
        .user-indicator-text { font-weight: 600; color: #0056b3; }
        .own-listing { background: #fff3cd; border-color: #ffc107; }
        .own-listing-badge { background: #ffc107; color: #856404; padding: 3px 10px; border-radius: 10px; font-size: 0.8em; font-weight: 600; margin-left: 10px; }
        .owned-title { background: #e7f3ff; border-color: #007bff; }
        .owned-badge { background: #007bff; color: white; padding: 3px 10px; border-radius: 10px; font-size: 0.8em; font-weight: 600; margin-left: 10px; }
        .status-badge { display: inline-block; padding: 5px 15px; border-radius: 15px; font-weight: 600; font-size: 0.85em; }
        .status-forsale { background: #d4edda; color: #155724; }
        .status-transferred { background: #d1ecf1; color: #0c5460; }
        .empty-state { text-align: center; padding: 50px; color: #666; }
        .empty-state h3 { margin-bottom: 15px; color: #333; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.6); }
        .modal-content { background-color: white; margin: 5% auto; padding: 30px; border-radius: 15px; max-width: 900px; max-height: 80vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #2c5282; }
        .modal-header h2 { color: #2c5282; margin: 0; }
        .close-modal { font-size: 32px; font-weight: bold; color: #666; cursor: pointer; }
        .close-modal:hover { color: #dc3545; }
        .history-section { background: #f0f4f8; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #2c5282; }
        .history-title { font-size: 1.2em; font-weight: 700; color: #2c5282; margin-bottom: 15px; }
        .history-item { background: white; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #6c757d; }
        .history-item.origin { border-left-color: #ffc107; background: #fff9e6; }
        .history-item.current { border-left-color: #28a745; background: #e6f7e9; }
        .filter-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }
        .filter-bar h2 { color: #2c5282; margin: 0; }
        .filter-select { padding: 8px 12px; border: 2px solid #dee2e6; border-radius: 6px; font-size: 0.9em; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Grain Title Tracking System</h1>
            <div class="user-info">
                <span id="userEmail"></span> | Role: <span id="userRole"></span>
            </div>
        </div>
        <div class="nav-buttons">
            <button class="nav-btn btn-primary" onclick="loadSales()">Marketplace</button>
            <button class="nav-btn btn-purple" onclick="loadMyTitles()">My Titles</button>
            <button class="nav-btn btn-success" onclick="showListSaleForm()">List New Sale</button>
            <button class="nav-btn btn-warning" onclick="loadAdminStats()" id="adminBtn" style="display:none;">Admin Stats</button>
            <button class="nav-btn btn-danger" onclick="logout()">Logout</button>
        </div>
        <div id="content" class="content">
            <div class="loading">Loading...</div>
        </div>
    </div>
    <div id="historyModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Complete Ownership History</h2>
                <span class="close-modal" onclick="closeHistoryModal()">&times;</span>
            </div>
            <div id="modalHistoryContent"></div>
        </div>
    </div>
    <script>
        var token = sessionStorage.getItem("id_token");
        var email = sessionStorage.getItem("user_email") || "";
        var role = sessionStorage.getItem("user_role") || "";
        if (!token) { window.location.href = "/"; }
        document.getElementById("userEmail").textContent = email || "Unknown";
        document.getElementById("userRole").textContent = role || "User";
        if (role === "Admin") { document.getElementById("adminBtn").style.display = "block"; }
        var grainPrices = {"Corn": 4.85, "Wheat": 6.25, "Soybean": 13.50, "Oats": 3.75};
        
        loadSales();

        function loadAdminStats() {
            document.getElementById("content").innerHTML = '<div class="loading">Loading statistics...</div>';
            fetch("/admin-stats", { headers: { "Authorization": token } })
            .then(function(res) { if (res.status === 403) { throw new Error("Forbidden"); } return res.json(); })
            .then(function(stats) {
                var html = '<h2 style="color:#2c5282;margin-bottom:25px;">System Statistics</h2>';
                html += '<div class="item-card"><h3>System Overview</h3><div class="item-details">';
                html += '<div class="detail-row"><span class="detail-label">Total Titles Issued</span><span class="detail-value">' + stats.system_stats.total_titles + '</span></div>';
                html += '<div class="detail-row"><span class="detail-label">Original Titles</span><span class="detail-value">' + stats.system_stats.original_titles + '</span></div>';
                html += '</div></div>';
                html += '<div class="item-card"><h3>Status Breakdown</h3><div class="item-details">';
                html += '<div class="detail-row"><span class="detail-label">For Sale</span><span class="detail-value">' + stats.status_breakdown.for_sale + '</span></div>';
                html += '</div></div>';
                html += '<div class="item-card"><h3>Grain Distribution Transfers By Type</h3><div class="item-details">';
                for (var grain in stats.grain_type_breakdown) {
                    html += '<div class="detail-row"><span class="detail-label">' + grain + '</span><span class="detail-value">' + stats.grain_type_breakdown[grain] + '</span></div>';
                }
                html += '</div></div>';
                html += '<div class="item-card"><h3>Volume Statistics</h3><div class="item-details">';
                html += '<div class="detail-row"><span class="detail-label">Total Bushels</span><span class="detail-value">' + stats.volume_stats.total_bushels.toLocaleString() + '</span></div>';
                html += '<div class="detail-row"><span class="detail-label">Total Value</span><span class="detail-value">$' + stats.volume_stats.total_value_usd.toLocaleString() + '</span></div>';
                html += '<div class="detail-row"><span class="detail-label">Avg Price/Bushel</span><span class="detail-value">$' + stats.volume_stats.average_price_per_bushel.toFixed(2) + '</span></div>';
                html += '</div></div>';
                document.getElementById("content").innerHTML = html;
            })
            .catch(function(err) { document.getElementById("content").innerHTML = '<div class="alert alert-danger">Error: ' + err.message + '</div>'; });
        }

        function showHistoryModal(titleHash, grainType) {
            document.getElementById("modalHistoryContent").innerHTML = '<div class="loading">Loading history...</div>';
            document.getElementById("historyModal").style.display = "block";
            fetch("/ownership-history", { method: "POST", headers: { "Content-Type": "application/json", "Authorization": token }, body: JSON.stringify({ title_hash: titleHash }) })
            .then(function(res) { return res.json(); })
            .then(function(response) {
                var history = response.ownership_history || [];
                var html = "";
                if (history.length > 0) {
                    html = '<div class="history-section"><div class="history-title">' + history.length + ' Record(s) in Chain - ' + grainType + '</div>';
                    history.forEach(function(record, index) {
                        var itemClass = record.is_current ? "current" : (index === 0 ? "origin" : "");
                        html += '<div class="history-item ' + itemClass + '">';
                        html += '<div><span class="history-label">Transfer #:</span> ' + record.transfer_count + '</div>';
                        html += '<div><span class="history-label">Owner:</span> ' + (record.owner || "Unknown") + '</div>';
                        if (record.sold_to) {
                            html += '<div><span class="history-label">Sold To:</span> ' + record.sold_to + '</div>';
                        }
                        html += '<div><span class="history-label">Price:</span> $' + (record.price || 0).toFixed(2) + '/bu</div>';
                        html += '<div><span class="history-label">Status:</span> ' + (record.status || "Unknown") + '</div>';
                        html += '<div><span class="history-label">Date:</span> ' + (record.timestamp_readable || "Unknown") + '</div>';
                        html += '<div class="hash-info"><div class="hash-label">Hash:</div><div class="hash-value">' + record.hash + '</div></div>';
                        html += '</div>';
                    });
                    html += '</div>';
                } else { html = "<p>No history available.</p>"; }
                document.getElementById("modalHistoryContent").innerHTML = html;
            })
            .catch(function(err) { document.getElementById("modalHistoryContent").innerHTML = "<p>Error: " + err.message + "</p>"; });
        }

        function closeHistoryModal() { document.getElementById("historyModal").style.display = "none"; }
        window.onclick = function(event) { if (event.target == document.getElementById("historyModal")) { closeHistoryModal(); } };

        function validateTitle(titleHash, elementId) {
            fetch("/validate-hash", { method: "POST", headers: { "Content-Type": "application/json", "Authorization": token }, body: JSON.stringify({ title_hash: titleHash, validate_full_chain: true }) })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                var el = document.getElementById(elementId);
                if (el) {
                    if (data.chain_valid) {
                        el.textContent = "Valid";
                        el.className = "validation-status status-valid";
                    } else {
                        el.textContent = "Invalid";
                        el.className = "validation-status status-invalid";
                    }
                }
            })
            .catch(function(err) {
                var el = document.getElementById(elementId);
                if (el) { el.textContent = "Error"; el.className = "validation-status status-invalid"; }
            });
        }

        function loadSales() {
            document.getElementById("content").innerHTML = '<div class="loading">Loading marketplace...</div>';
            fetch("/sales", { headers: { "Authorization": token } })
            .then(function(res) { return res.json(); })
            .then(function(response) {
                var data = response.items || response.Items || response;
                if (!Array.isArray(data)) data = [];
                if (data.length === 0) {
                    document.getElementById("content").innerHTML = '<div class="empty-state"><h3>No Titles for Sale</h3><p>Check back later or list your own.</p></div>';
                    return;
                }
                var html = '<div class="filter-bar"><h2>Marketplace - Titles For Sale</h2>';
                html += '<div><label style="margin-right:10px;font-weight:600;color:#666;">Filter by Grain:</label>';
                html += '<select class="filter-select" id="grainFilter" onchange="filterByGrain()">';
                html += '<option value="">All Grain Types</option><option value="Corn">Corn</option><option value="Wheat">Wheat</option><option value="Soybean">Soybean</option><option value="Oats">Oats</option>';
                html += '</select></div></div>';
                data.forEach(function(item, idx) {
                    var grainType = item.GrainType || "Unknown";
                    var grainClass = "grain-" + grainType.toLowerCase();
                    var quantity = parseInt(item.Quantity) || 0;
                    var price = parseFloat(item.Price) || 0;
                    var totalValue = quantity * price;
                    var sellerId = item.SellerID || item.SellerId || item.CreatedBy || "";
                    var buyerId = item.BuyerID || "NONE";
                    var status = item.Status || "";
                    var titleHash = item.TitleHash;
                    var currentHash = item.CurrentHash || item.TitleHash;
                    var isOwnListing = (sellerId.toLowerCase() === email.toLowerCase() && status === "ForSale" && buyerId === "NONE");
                    var youOwnThis = (buyerId.toLowerCase() === email.toLowerCase() && status === "Transferred");
                    var validId = "valid-" + idx;
                    var cardClass = isOwnListing ? "own-listing" : (youOwnThis ? "owned-title" : "");
                    var badge = isOwnListing ? '<span class="own-listing-badge">Your Listing</span>' : (youOwnThis ? '<span class="owned-badge">You Own This</span>' : '');
                    html += '<div class="item-card ' + cardClass + '" data-grain="' + grainType + '">';
                    html += '<div class="item-header"><h3>' + sellerId + badge + '</h3>';
                    html += '<span class="validation-status status-checking" id="' + validId + '">Checking...</span></div>';
                    html += '<div class="item-details">';
                    var ownerId = (status === "Transferred") ? buyerId : sellerId;
                    html += '<div class="detail-row"><span class="detail-label">Owner ID</span><span class="detail-value">' + ownerId + '</span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Grain Type</span><span class="detail-value"><span class="grain-badge ' + grainClass + '">' + grainType + '</span></span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Quantity</span><span class="detail-value">' + quantity.toLocaleString() + ' Bushels</span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Price</span><span class="detail-value">$' + price.toFixed(2) + '/bu</span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Total Value</span><span class="detail-value">$' + totalValue.toLocaleString(undefined, {minimumFractionDigits:2}) + '</span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Transfers</span><span class="detail-value">' + (item.TransferCount || 0) + '</span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Status</span><span class="detail-value"><span class="status-badge status-' + status.toLowerCase() + '">' + status + '</span></span></div>';
                    html += '</div>';
                    html += '<div class="hash-info hash-clickable" onclick="showHistoryModal(\'' + titleHash + '\', \'' + grainType + '\')"><div class="hash-label">Current Hash:</div><div class="hash-value">' + currentHash + '</div><div class="hash-hint">Click to see complete ownership history</div></div>';
                    html += '<div style="margin-top:15px;">';
                    if (isOwnListing) {
                        html += '<button class="action-btn buy-btn" disabled>Your Listing</button>';
                    } else if (youOwnThis) {
                        html += '<button class="action-btn buy-btn" disabled>You Own This</button>';
                    } else if (status === "ForSale") {
                        html += '<button class="action-btn buy-btn" onclick="showBuyForm(\'' + titleHash + '\', \'' + grainType + '\', ' + quantity + ', ' + price + ')">Buy This Title</button>';
                    } else {
                        html += '<button class="action-btn buy-btn" disabled>Not For Sale</button>';
                    }
                    html += '</div></div>';
                });
                document.getElementById("content").innerHTML = html;
                data.forEach(function(item, idx) {
                    var currentHash = item.CurrentHash || item.TitleHash;
                    validateTitle(currentHash, "valid-" + idx);
                });
            })
            .catch(function(err) { document.getElementById("content").innerHTML = '<div class="alert alert-danger">Error: ' + err.message + '</div>'; });
        }

        function filterByGrain() {
            var filter = document.getElementById("grainFilter").value;
            var cards = document.querySelectorAll(".item-card");
            cards.forEach(function(card) {
                var grain = card.getAttribute("data-grain");
                if (!filter || grain === filter) { card.style.display = "block"; }
                else { card.style.display = "none"; }
            });
        }

        function filterMyTitlesByGrain() {
            var filter = document.getElementById("myTitlesGrainFilter").value;
            var cards = document.querySelectorAll(".item-card");
            cards.forEach(function(card) {
                var grain = card.getAttribute("data-grain");
                if (!filter || grain === filter) { card.style.display = "block"; }
                else { card.style.display = "none"; }
            });
        }

        function loadMyTitles() {
            document.getElementById("content").innerHTML = '<div class="loading">Loading your titles...</div>';
            fetch("/my-titles", { headers: { "Authorization": token } })
            .then(function(res) { return res.json(); })
            .then(function(response) {
                var data = response.items || response.Items || response;
                if (!Array.isArray(data)) data = [];
                if (data.length === 0) {
                    document.getElementById("content").innerHTML = '<div class="empty-state"><h3>No Titles Owned</h3><p>Visit the Marketplace to purchase grain titles.</p><button class="nav-btn btn-primary" onclick="loadSales()" style="margin-top:20px;">Go to Marketplace</button></div>';
                    return;
                }
                var html = '<div class="filter-bar"><h2>My Titles</h2>';
                html += '<div><label style="margin-right:10px;font-weight:600;color:#666;">Filter by Grain:</label>';
                html += '<select class="filter-select" id="myTitlesGrainFilter" onchange="filterMyTitlesByGrain()">';
                html += '<option value="">All Grain Types</option><option value="Corn">Corn</option><option value="Wheat">Wheat</option><option value="Soybean">Soybean</option><option value="Oats">Oats</option>';
                html += '</select></div></div>';
                data.forEach(function(item) {
                    var grainType = item.GrainType || "Unknown";
                    var grainClass = "grain-" + grainType.toLowerCase();
                    var quantity = parseInt(item.Quantity) || 0;
                    var price = parseFloat(item.Price) || 0;
                    var totalValue = quantity * price;
                    var status = item.Status || "Unknown";
                    var titleHash = item.TitleHash || item.CurrentHash;
                    var canRelist = (status === "Transferred");
                    html += '<div class="item-card owned-title" data-grain="' + grainType + '">';
                    html += '<div class="item-header"><h3>' + grainType + ' - ' + quantity.toLocaleString() + ' Bushels<span class="owned-badge">You Own This</span></h3>';
                    html += '<span class="status-badge status-' + status.toLowerCase() + '">' + status + '</span></div>';
                    html += '<div class="item-details">';
                    html += '<div class="detail-row"><span class="detail-label">Grain Type</span><span class="detail-value"><span class="grain-badge ' + grainClass + '">' + grainType + '</span></span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Quantity</span><span class="detail-value">' + quantity.toLocaleString() + ' Bushels</span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Price</span><span class="detail-value">$' + price.toFixed(2) + '/bu</span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Total Value</span><span class="detail-value">$' + totalValue.toLocaleString(undefined, {minimumFractionDigits:2}) + '</span></div>';
                    html += '<div class="detail-row"><span class="detail-label">Transfers</span><span class="detail-value">' + (item.TransferCount || 0) + '</span></div>';
                    html += '</div>';
                    html += '<div class="hash-info hash-clickable" onclick="showHistoryModal(\'' + titleHash + '\', \'' + grainType + '\')"><div class="hash-label">Current Hash:</div><div class="hash-value">' + titleHash + '</div></div>';
                    html += '<div style="margin-top:15px;">';
                    if (canRelist) {
                        html += '<button class="action-btn relist-btn" onclick="showRelistForm(\'' + titleHash + '\', \'' + grainType + '\', ' + quantity + ', ' + price + ')">Relist for Sale</button>';
                    } else {
                        html += '<button class="action-btn relist-btn" disabled>Already For Sale</button>';
                    }
                    html += '</div></div>';
                });
                document.getElementById("content").innerHTML = html;
            })
            .catch(function(err) { document.getElementById("content").innerHTML = '<div class="alert alert-danger">Error: ' + err.message + '</div>'; });
        }

        function showListSaleForm() {
            var html = '<div class="form-container"><h2 style="color:#2c5282;margin-bottom:25px;">List New Grain Title for Sale</h2>';
            html += '<div class="user-indicator"><span>&#x1F464;</span><span class="user-indicator-text">Listing as: ' + email + '</span></div>';
            html += '<form onsubmit="submitNewSale(event)">';
            html += '<div class="form-group"><label>Grain Type *</label><select id="grainType" required onchange="updatePriceFromMarket()"><option value="">Select grain type</option><option value="Corn">Corn</option><option value="Wheat">Wheat</option><option value="Soybean">Soybean</option><option value="Oats">Oats</option></select></div>';
            html += '<div class="form-group"><label>Quantity (Bushels) *</label><input type="number" id="quantity" required min="1" placeholder="Enter quantity"></div>';
            html += '<div class="form-group"><label>Price per Bushel ($) *</label><input type="number" id="price" required min="0" step="0.01" placeholder="Enter price"><div class="price-hint" id="priceHint"></div></div>';
            html += '<div class="form-actions"><button type="submit" class="nav-btn btn-success">List for Sale</button><button type="button" class="nav-btn btn-secondary" onclick="loadSales()">Cancel</button></div>';
            html += '</form></div>';
            document.getElementById("content").innerHTML = html;
        }

        function updatePriceFromMarket() {
            var grainType = document.getElementById("grainType").value;
            if (grainType && grainPrices[grainType]) {
                document.getElementById("price").value = grainPrices[grainType].toFixed(2);
                document.getElementById("priceHint").textContent = "Market price: $" + grainPrices[grainType].toFixed(2) + "/bushel";
            }
        }

        function submitNewSale(event) {
            event.preventDefault();
            var data = { grain_type: document.getElementById("grainType").value, quantity: parseInt(document.getElementById("quantity").value), price: parseFloat(document.getElementById("price").value) };
            fetch("/titles", { method: "POST", headers: { "Content-Type": "application/json", "Authorization": token }, body: JSON.stringify(data) })
            .then(function(res) { return res.json(); })
            .then(function(result) {
                if (result.error) { alert("Error: " + result.error); return; }
                var html = '<div class="form-container"><div class="alert alert-success"><h3>Title Listed Successfully!</h3>';
                html += '<p><strong>Seller:</strong> ' + (result.seller_id || email) + '</p>';
                html += '<p><strong>Grain:</strong> ' + data.grain_type + '</p>';
                html += '<p><strong>Quantity:</strong> ' + data.quantity.toLocaleString() + ' bushels</p>';
                html += '<p><strong>Price:</strong> $' + data.price.toFixed(2) + ' per bushel</p></div>';
                html += '<div class="hash-info"><div class="hash-label">Title Hash:</div><div class="hash-value">' + (result.hash || result.titleId) + '</div></div>';
                html += '<div class="form-actions"><button class="nav-btn btn-primary" onclick="loadSales()">View Marketplace</button><button class="nav-btn btn-success" onclick="showListSaleForm()">List Another</button></div></div>';
                document.getElementById("content").innerHTML = html;
            })
            .catch(function(err) { alert("Error: " + err.message); });
        }

        function showBuyForm(titleHash, grainType, quantity, price) {
            var totalValue = quantity * price;
            var html = '<div class="form-container"><h2 style="color:#2c5282;margin-bottom:25px;">Purchase Title</h2>';
            html += '<div class="user-indicator"><span>&#x1F6D2;</span><span class="user-indicator-text">Buying as: ' + email + '</span></div>';
            html += '<div class="alert alert-info"><p><strong>Purchasing:</strong> ' + grainType + ' - ' + quantity.toLocaleString() + ' Bushels</p>';
            html += '<p><strong>Price:</strong> $' + price.toFixed(2) + ' per bushel</p>';
            html += '<p><strong>Total Cost:</strong> $' + totalValue.toLocaleString(undefined, {minimumFractionDigits:2}) + '</p></div>';
            html += '<div class="hash-info"><div class="hash-label">Title Hash:</div><div class="hash-value">' + titleHash + '</div></div>';
            html += '<div class="form-actions"><button class="nav-btn btn-success" onclick="submitPurchase(\'' + titleHash + '\')">Confirm Purchase</button><button class="nav-btn btn-secondary" onclick="loadSales()">Cancel</button></div></div>';
            document.getElementById("content").innerHTML = html;
        }

        function submitPurchase(titleHash) {
            fetch("/transfer-title", { method: "POST", headers: { "Content-Type": "application/json", "Authorization": token }, body: JSON.stringify({ title_hash: titleHash }) })
            .then(function(res) { return res.json(); })
            .then(function(result) {
                if (result.error) { alert("Error: " + result.error); return; }
                var html = '<div class="form-container"><div class="alert alert-success"><h3>Title Purchased Successfully!</h3>';
                html += '<p><strong>Buyer:</strong> ' + (result.buyer_id || email) + '</p>';
                html += '<p><strong>Previous Owner:</strong> ' + (result.seller_id || "Unknown") + '</p>';
                html += '<p><strong>Transfer #:</strong> ' + (result.transfer_count || 1) + '</p></div>';
                html += '<div class="hash-info"><div class="hash-label">New Hash:</div><div class="hash-value">' + (result.new_hash || titleHash) + '</div></div>';
                html += '<div class="form-actions"><button class="nav-btn btn-purple" onclick="loadMyTitles()">View My Titles</button><button class="nav-btn btn-primary" onclick="loadSales()">Back to Marketplace</button></div></div>';
                document.getElementById("content").innerHTML = html;
            })
            .catch(function(err) { alert("Error: " + err.message); });
        }

        function showRelistForm(titleHash, grainType, quantity, currentPrice) {
            var defaultPrice = grainPrices[grainType] || currentPrice;
            var html = '<div class="form-container"><h2 style="color:#2c5282;margin-bottom:25px;">Relist Title for Sale</h2>';
            html += '<div class="user-indicator"><span>&#x1F4B0;</span><span class="user-indicator-text">Listing as: ' + email + '</span></div>';
            html += '<div class="alert alert-info"><p><strong>Relisting:</strong> ' + grainType + ' - ' + quantity.toLocaleString() + ' Bushels</p></div>';
            html += '<div class="hash-info"><div class="hash-label">Title Hash:</div><div class="hash-value">' + titleHash + '</div></div>';
            html += '<form onsubmit="submitRelist(event, \'' + titleHash + '\')">';
            html += '<div class="form-group"><label>New Price per Bushel ($) *</label><input type="number" id="newPrice" required min="0" step="0.01" value="' + defaultPrice.toFixed(2) + '"><div class="price-hint">Market price: $' + defaultPrice.toFixed(2) + '/bushel</div></div>';
            html += '<div class="form-actions"><button type="submit" class="nav-btn btn-success">List for Sale</button><button type="button" class="nav-btn btn-secondary" onclick="loadMyTitles()">Cancel</button></div>';
            html += '</form></div>';
            document.getElementById("content").innerHTML = html;
        }

        function submitRelist(event, titleHash) {
            event.preventDefault();
            var data = { title_hash: titleHash, new_price: parseFloat(document.getElementById("newPrice").value) };
            fetch("/relist-title", { method: "POST", headers: { "Content-Type": "application/json", "Authorization": token }, body: JSON.stringify(data) })
            .then(function(res) { return res.json(); })
            .then(function(result) {
                if (result.error) { alert("Error: " + result.error); return; }
                var html = '<div class="form-container"><div class="alert alert-success"><h3>Title Listed for Sale!</h3>';
                html += '<p><strong>New Price:</strong> $' + data.new_price.toFixed(2) + ' per bushel</p></div>';
                html += '<div class="form-actions"><button class="nav-btn btn-primary" onclick="loadSales()">View Marketplace</button><button class="nav-btn btn-purple" onclick="loadMyTitles()">View My Titles</button></div></div>';
                document.getElementById("content").innerHTML = html;
            })
            .catch(function(err) { alert("Error: " + err.message); });
        }

        function logout() { sessionStorage.clear(); window.location.href = "/"; }
    </script>
</body>
</html>'''
    }