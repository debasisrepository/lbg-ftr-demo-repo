import { RadioButtonGroup, RadioButton } from '@carbon/react';
import styles from './HandoffChooser.module.css';

interface ChannelOption {
  value: string;
  label: string;
  description: string;
}

interface HandoffChooserProps {
  value: string;
  onChange: (value: string) => void;
  options: ChannelOption[];
}

/**
 * Radio button group for choosing a channel to continue in
 */
export function HandoffChooser({ value, onChange, options }: HandoffChooserProps) {
  return (
    <RadioButtonGroup
      legendText="Continue this Case in"
      name="to_channel"
      valueSelected={value}
      onChange={(selectedValue: string | number | undefined) => {
        if (typeof selectedValue === 'string') {
          onChange(selectedValue);
        }
      }}
      orientation="vertical"
      className={styles.radioGroup}
    >
      {options.map((option) => (
        <RadioButton
          key={option.value}
          id={`channel-${option.value}`}
          value={option.value}
          labelText={
            <div>
              <div className="cds--productive-heading-01">
                {option.label}
              </div>
              <div className={`cds--label-01 ${styles.descriptionText}`}>
                {option.description}
              </div>
            </div>
          }
        />
      ))}
    </RadioButtonGroup>
  );
}
