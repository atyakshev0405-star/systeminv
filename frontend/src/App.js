import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [inventory, setInventory] = useState([]);
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    category: 'medication',
    quantity: '',
    unit: 'шт',
    manufacturer: '',
    batch_number: '',
    expiry_date: '',
    cost_per_unit: '',
    supplier: '',
    location: '',
    description: '',
    min_quantity_threshold: '10'
  });

  // Fetch data functions
  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const url = selectedCategory 
        ? `${API_BASE}/api/inventory?category=${selectedCategory}`
        : `${API_BASE}/api/inventory`;
      const response = await fetch(url);
      const data = await response.json();
      setInventory(data);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/alerts`);
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const searchInventory = async (term) => {
    if (!term.trim()) {
      fetchInventory();
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/inventory/search?q=${encodeURIComponent(term)}`);
      const data = await response.json();
      setInventory(data);
    } catch (error) {
      console.error('Error searching inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  // CRUD operations
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem 
        ? `${API_BASE}/api/inventory/${editingItem.id}`
        : `${API_BASE}/api/inventory`;
      
      const method = editingItem ? 'PUT' : 'POST';
      
      const dataToSend = {
        ...formData,
        quantity: parseInt(formData.quantity) || 0,
        cost_per_unit: parseFloat(formData.cost_per_unit) || null,
        min_quantity_threshold: parseInt(formData.min_quantity_threshold) || 10
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend),
      });

      if (response.ok) {
        setShowAddModal(false);
        setEditingItem(null);
        resetForm();
        fetchInventory();
        fetchStats();
      }
    } catch (error) {
      console.error('Error saving item:', error);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name || '',
      category: item.category || 'medication',
      quantity: item.quantity?.toString() || '',
      unit: item.unit || 'шт',
      manufacturer: item.manufacturer || '',
      batch_number: item.batch_number || '',
      expiry_date: item.expiry_date || '',
      cost_per_unit: item.cost_per_unit?.toString() || '',
      supplier: item.supplier || '',
      location: item.location || '',
      description: item.description || '',
      min_quantity_threshold: item.min_quantity_threshold?.toString() || '10'
    });
    setShowAddModal(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Вы уверены, что хотите удалить этот элемент?')) {
      try {
        const response = await fetch(`${API_BASE}/api/inventory/${id}`, {
          method: 'DELETE',
        });
        if (response.ok) {
          fetchInventory();
          fetchStats();
        }
      } catch (error) {
        console.error('Error deleting item:', error);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      category: 'medication',
      quantity: '',
      unit: 'шт',
      manufacturer: '',
      batch_number: '',
      expiry_date: '',
      cost_per_unit: '',
      supplier: '',
      location: '',
      description: '',
      min_quantity_threshold: '10'
    });
  };

  const openAddModal = () => {
    setEditingItem(null);
    resetForm();
    setShowAddModal(true);
  };

  // Status color mapping
  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-emerald-400';
      case 'low_stock': return 'text-yellow-400';
      case 'expired': return 'text-red-400';
      case 'out_of_stock': return 'text-gray-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      'active': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      'low_stock': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      'expired': 'bg-red-500/20 text-red-400 border-red-500/30',
      'out_of_stock': 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    };
    
    const labels = {
      'active': 'Активен',
      'low_stock': 'Заканчивается',
      'expired': 'Просрочен',
      'out_of_stock': 'Отсутствует'
    };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full border ${colors[status] || colors.active}`}>
        {labels[status] || status}
      </span>
    );
  };

  // Category translation
  const categoryLabels = {
    'medication': 'Медикаменты',
    'equipment': 'Оборудование',
    'consumable': 'Расходные материалы'
  };

  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchStats();
      fetchAlerts();
    } else if (activeTab === 'inventory') {
      fetchInventory();
    }
  }, [activeTab, selectedCategory]);

  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (searchTerm && activeTab === 'inventory') {
        searchInventory(searchTerm);
      } else if (!searchTerm && activeTab === 'inventory') {
        fetchInventory();
      }
    }, 300);

    return () => clearTimeout(delayedSearch);
  }, [searchTerm]);

  const renderDashboard = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-2">
          СтолицаЗдоровья
        </h1>
        <p className="text-gray-400">Система автоматизированной инвентаризации</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="cyber-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Всего позиций</p>
                <p className="text-2xl font-bold text-white">{stats.total_items}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                📦
              </div>
            </div>
          </div>
          
          <div className="cyber-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Заканчиваются</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.low_stock_items}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-lg flex items-center justify-center">
                ⚠️
              </div>
            </div>
          </div>
          
          <div className="cyber-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Просрочены</p>
                <p className="text-2xl font-bold text-red-400">{stats.expired_items}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-pink-500 rounded-lg flex items-center justify-center">
                🚫
              </div>
            </div>
          </div>
          
          <div className="cyber-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Общая стоимость</p>
                <p className="text-2xl font-bold text-emerald-400">₽{stats.total_value?.toFixed(2) || '0.00'}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-lg flex items-center justify-center">
                💰
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alerts Section */}
      {alerts && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Low Stock Alerts */}
          <div className="cyber-card p-6">
            <h3 className="text-lg font-semibold text-yellow-400 mb-4 flex items-center">
              ⚠️ Заканчиваются ({alerts.low_stock?.length || 0})
            </h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {alerts.low_stock?.map((item) => (
                <div key={item.id} className="flex justify-between items-center p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                  <div>
                    <p className="font-medium text-white text-sm">{item.name}</p>
                    <p className="text-xs text-gray-400">{categoryLabels[item.category]}</p>
                  </div>
                  <span className="text-yellow-400 font-bold">{item.quantity} {item.unit}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Expired Alerts */}
          <div className="cyber-card p-6">
            <h3 className="text-lg font-semibold text-red-400 mb-4 flex items-center">
              🚫 Просрочены ({alerts.expired?.length || 0})
            </h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {alerts.expired?.map((item) => (
                <div key={item.id} className="flex justify-between items-center p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                  <div>
                    <p className="font-medium text-white text-sm">{item.name}</p>
                    <p className="text-xs text-gray-400">{item.expiry_date}</p>
                  </div>
                  <span className="text-red-400 font-bold">{item.quantity} {item.unit}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Expiring Soon Alerts */}
          <div className="cyber-card p-6">
            <h3 className="text-lg font-semibold text-orange-400 mb-4 flex items-center">
              ⏰ Скоро истекут ({alerts.expiring_soon?.length || 0})
            </h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {alerts.expiring_soon?.map((item) => (
                <div key={item.id} className="flex justify-between items-center p-3 bg-orange-500/10 rounded-lg border border-orange-500/20">
                  <div>
                    <p className="font-medium text-white text-sm">{item.name}</p>
                    <p className="text-xs text-gray-400">{item.expiry_date}</p>
                  </div>
                  <span className="text-orange-400 font-bold">{item.quantity} {item.unit}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderInventory = () => (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-white">Управление инвентарем</h2>
        <button
          onClick={openAddModal}
          className="cyber-button-primary px-6 py-2 rounded-lg"
        >
          ➕ Добавить позицию
        </button>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="🔍 Поиск по названию, производителю, партии..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="cyber-input w-full"
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="cyber-select"
        >
          <option value="">Все категории</option>
          <option value="medication">Медикаменты</option>
          <option value="equipment">Оборудование</option>
          <option value="consumable">Расходные материалы</option>
        </select>
      </div>

      {/* Inventory Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-400 mt-2">Загрузка...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {inventory.map((item) => (
            <div key={item.id} className="cyber-card p-6 hover:border-blue-500/50 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-white">{item.name}</h3>
                  <p className="text-sm text-gray-400">{categoryLabels[item.category]}</p>
                </div>
                <div className="text-right">
                  {getStatusBadge(item.status)}
                </div>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Количество:</span>
                  <span className={`font-medium ${item.quantity <= item.min_quantity_threshold ? 'text-yellow-400' : 'text-white'}`}>
                    {item.quantity} {item.unit}
                  </span>
                </div>
                
                {item.manufacturer && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Производитель:</span>
                    <span className="text-white">{item.manufacturer}</span>
                  </div>
                )}
                
                {item.expiry_date && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Срок годности:</span>
                    <span className={`${new Date(item.expiry_date) < new Date() ? 'text-red-400' : 
                      new Date(item.expiry_date) < new Date(Date.now() + 30*24*60*60*1000) ? 'text-orange-400' : 'text-white'}`}>
                      {new Date(item.expiry_date).toLocaleDateString('ru-RU')}
                    </span>
                  </div>
                )}
                
                {item.location && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Расположение:</span>
                    <span className="text-white">{item.location}</span>
                  </div>
                )}
              </div>
              
              <div className="flex gap-2 mt-4 pt-4 border-t border-gray-700">
                <button
                  onClick={() => handleEdit(item)}
                  className="flex-1 cyber-button-secondary text-xs py-2"
                >
                  ✏️ Редактировать
                </button>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="flex-1 cyber-button-danger text-xs py-2"
                >
                  🗑️ Удалить
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {inventory.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">📦</div>
          <p className="text-gray-400">Нет элементов инвентаря</p>
          <button
            onClick={openAddModal}
            className="cyber-button-primary px-6 py-2 rounded-lg mt-4"
          >
            Добавить первую позицию
          </button>
        </div>
      )}
    </div>
  );

  const renderModal = () => {
    if (!showAddModal) return null;

    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div className="cyber-card w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white">
                {editingItem ? 'Редактировать позицию' : 'Добавить новую позицию'}
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Название *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Категория *</label>
                  <select
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    className="cyber-select w-full"
                  >
                    <option value="medication">Медикаменты</option>
                    <option value="equipment">Оборудование</option>
                    <option value="consumable">Расходные материалы</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Количество *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    value={formData.quantity}
                    onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Единица измерения</label>
                  <input
                    type="text"
                    value={formData.unit}
                    onChange={(e) => setFormData({...formData, unit: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Производитель</label>
                  <input
                    type="text"
                    value={formData.manufacturer}
                    onChange={(e) => setFormData({...formData, manufacturer: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Номер партии</label>
                  <input
                    type="text"
                    value={formData.batch_number}
                    onChange={(e) => setFormData({...formData, batch_number: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Срок годности</label>
                  <input
                    type="date"
                    value={formData.expiry_date}
                    onChange={(e) => setFormData({...formData, expiry_date: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Стоимость за единицу</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.cost_per_unit}
                    onChange={(e) => setFormData({...formData, cost_per_unit: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Поставщик</label>
                  <input
                    type="text"
                    value={formData.supplier}
                    onChange={(e) => setFormData({...formData, supplier: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Расположение</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({...formData, location: e.target.value})}
                    className="cyber-input w-full"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Минимальный остаток</label>
                <input
                  type="number"
                  min="0"
                  value={formData.min_quantity_threshold}
                  onChange={(e) => setFormData({...formData, min_quantity_threshold: e.target.value})}
                  className="cyber-input w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Описание</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="cyber-input w-full h-20 resize-none"
                />
              </div>
              
              <div className="flex gap-4 pt-4">
                <button
                  type="submit"
                  className="flex-1 cyber-button-primary py-3"
                >
                  {editingItem ? '💾 Обновить' : '➕ Добавить'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 cyber-button-secondary py-3"
                >
                  ❌ Отменить
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Navigation */}
      <nav className="cyber-nav p-4 mb-8">
        <div className="container mx-auto flex justify-center">
          <div className="flex space-x-1 bg-gray-800/50 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-6 py-2 rounded-lg transition-all ${
                activeTab === 'dashboard'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              📊 Дашборд
            </button>
            <button
              onClick={() => setActiveTab('inventory')}
              className={`px-6 py-2 rounded-lg transition-all ${
                activeTab === 'inventory'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              📦 Инвентарь
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 pb-8">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'inventory' && renderInventory()}
      </main>

      {/* Modal */}
      {renderModal()}
    </div>
  );
}

export default App;