import { Checkmark, WarningAlt } from '@carbon/icons-react';
import styles from './LifelineGuidanceList.module.css';

interface LifelineItem {
  id: string;
  incident_reference: string;
  guidance_category: string;
  guidance_title: string;
  guidance_body: string;
  published_at: string;
}

interface LifelineGuidanceListProps {
  items: LifelineItem[];
  category: 'what_still_works' | 'what_is_affected' | 'protective_action';
  title: string;
}

/**
 * Display lifeline guidance grouped by category
 */
export function LifelineGuidanceList({
  items,
  category,
  title,
}: LifelineGuidanceListProps) {
  const categoryItems = items.filter((item) => item.guidance_category === category);
  
  if (categoryItems.length === 0) {
    return null;
  }
  
  const isPositive = category === 'what_still_works';
  const Icon = isPositive ? Checkmark : WarningAlt;
  const iconClass = isPositive ? 'cds--tag--green' : 'cds--tag--gold';
  
  return (
    <section className="cds--stack-scale-6" aria-labelledby={`${category}-h`}>
      <h2 className="cds--productive-heading-02" id={`${category}-h`}>
        {title}
      </h2>
      <ul className={`cds--stack-scale-3 ${styles.guidanceList}`}>
        {categoryItems.map((item) => (
          <li key={item.id} className={styles.guidanceItem}>
            <p className={`cds--productive-heading-01 ${styles.guidanceTitle}`}>
              <Icon size={16} className={iconClass} aria-hidden="true" />
              {item.guidance_title}
            </p>
            <p className={`cds--body-01 ${styles.guidanceBody}`}>
              {item.guidance_body}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
