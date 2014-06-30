package gov.nist.spectrumbrowser.client;

import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;

public class NameValueBox extends Composite {
	HorizontalPanel horizontalPanel;
	Label name;
	Label value;
	
	public NameValueBox(String name, String value) {
		horizontalPanel = new HorizontalPanel();
		initWidget(horizontalPanel);
		this.name = new Label();
		this.name.setStyleName("textName");
		this.value = new Label();
		this.value.setStyleName("textValue");
		this.name.setText(name);
		this.value.setText(value);
		this.value.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		horizontalPanel.add(this.name);
		horizontalPanel.add(this.value);
		
	}
	
	public void setValue(String value) {
		this.value.setText(value);
	
	}

	
	

}
