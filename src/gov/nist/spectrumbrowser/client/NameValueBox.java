/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
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
