import React from 'react';
import { ProposalCategory } from '../../types/governance';

interface CategoryFilterProps {
  categories?: ProposalCategory[];
  selectedCategory?: string;
  onSelectCategory?: (categoryId: string) => void;
}

const CategoryFilter: React.FC<CategoryFilterProps> = ({
  categories = [
    { id: 'treasury', name: 'Treasury', color: 'purple' },
    { id: 'governance', name: 'Governance', color: 'blue' },
    { id: 'protocol', name: 'Protocol', color: 'green' }
  ],
  selectedCategory = 'all',
  onSelectCategory = () => console.log('Category selected')
}) => {
  console.log('CategoryFilter rendered');
  
  const allCategory = { id: 'all', name: 'All Proposals', color: 'gray' };
  const allCategories = [allCategory, ...categories];
  
  return (
    <div data-cmp="CategoryFilter" className="flex flex-wrap gap-2">
      {allCategories.map((category) => (
        <button
          key={category.id}
          onClick={() => onSelectCategory(category.id)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            selectedCategory === category.id
              ? 'bg-gradient-to-r from-primary to-chart-2 text-primary-foreground shadow-custom'
              : 'bg-accent text-accent-foreground hover:bg-accent/80'
          }`}
        >
          {category.name}
        </button>
      ))}
    </div>
  );
};

export default CategoryFilter;