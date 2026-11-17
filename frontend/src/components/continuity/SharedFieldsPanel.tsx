import { Accordion, AccordionItem, Tag } from '@carbon/react';
import styles from './SharedFieldsPanel.module.css';

interface SharedFieldsPanelProps {
  shared_field_names: string[];
  package_version: number;
  generated_at: string;
}

/**
 * Display what fields will be shared with the receiving channel
 */
export function SharedFieldsPanel({
  shared_field_names,
  package_version,
  generated_at,
}: SharedFieldsPanelProps) {
  const generatedDate = new Date(generated_at);
  const formattedTime = generatedDate.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
  });
  
  return (
    <Accordion>
      <AccordionItem title="What will be shared">
        <div className="cds--stack-scale-5">
          <div className={styles.tagContainer}>
            {shared_field_names.map((field) => (
              <Tag key={field} type="outline">
                {field}
              </Tag>
            ))}
          </div>
          
          <p className={`cds--label-01 ${styles.metaText}`}>
            Prepared {formattedTime} · version {package_version}
          </p>
        </div>
      </AccordionItem>
    </Accordion>
  );
}
