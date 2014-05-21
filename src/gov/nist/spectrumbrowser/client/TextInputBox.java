package gov.nist.spectrumbrowser.client;

import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.ValueBoxBase.TextAlignment;

public class TextInputBox extends Composite {
	HorizontalPanel horizontalPanel;
	Label label;
	TextBox textBox;
	
	public TextInputBox(String label, String initialText) {
		horizontalPanel = new HorizontalPanel();
		initWidget(horizontalPanel);
		this.label = new Label();
		this.label.setStyleName("textName");	
		textBox = new TextBox();
		this.textBox.setStyleName("textValue");	
		this.label.setText(label);
		horizontalPanel.add(this.label);
		horizontalPanel.add(textBox);
		textBox.setText(initialText);
		textBox.setAlignment(TextAlignment.CENTER);		
	}
	
	public  boolean isInteger() {
			String str = getValue();
		    if (str == null) {
		            return false;
		    }
		    int length = str.length();
		    if (length == 0) {
		            return false;
		    }
		    int i = 0;
		    if (str.charAt(0) == '-') {
		            if (length == 1) {
		                    return false;
		            }
		            i = 1;
		    }
		    for (; i < length; i++) {
		            char c = str.charAt(i);
		            if (c <= '/' || c >= ':') {
		                    return false;
		            }
		    }
		    return true;
		
	}
	
	public boolean isNonNegative() {
		return isInteger() && Integer.parseInt(getValue()) >=0;
	}
	
	public String getText() {
		return textBox.getValue();
	}
	
	public void setValue(String value) {
		this.textBox.setValue(value);
	}
	
	public String getValue() {
		return this.textBox.getValue();
	}

	public void setEnabled(boolean b) {
		this.textBox.setEnabled(b);
	}

	public void addValueChangedHandler(final Runnable runnable, final int maxDays) {
		this.textBox.setTitle("Resticted to " + maxDays + " days.");
		this.textBox.addValueChangeHandler(new ValueChangeHandler<String> () {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String valueString = event.getValue();
				if (!isNonNegative()) {
					Window.alert("Value must be positive and less than " + maxDays);
					setValue("Specify");
				} else {
					int count = Integer.parseInt(valueString);
					if ( count < 1 || count > maxDays ) {
						Window.alert("Value must be in the range [1:" + maxDays +"]" );
						if ( count < 1) setValue("1");
						else setValue(Integer.toString(maxDays));
					} else {
						runnable.run();
					}
				}
				
			}
			
		});
	}

}
