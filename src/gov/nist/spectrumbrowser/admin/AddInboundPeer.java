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
package gov.nist.spectrumbrowser.admin;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class AddInboundPeer {
	
	private Admin admin;
	private InboundPeers inboundPeers;
	private VerticalPanel verticalPanel;
	private TextBox serverIdTextBox;
	private TextBox serverKeyTextBox;
	private TextBox commentTextBox;
	
	public AddInboundPeer(Admin admin, InboundPeers inboundPeers, VerticalPanel verticalPanel) {
		this.admin = admin;
		this.inboundPeers = inboundPeers;
		this.verticalPanel = verticalPanel;
	}
	
	public void draw() {
		verticalPanel.clear();
		HTML html = new HTML("<H2>Add peer for inbound registration (Registering server will send these credentials).</H2>");
		verticalPanel.add(html);
		Grid grid = new Grid(3,2);
		grid.setText(0, 0, "Server ID");
		serverIdTextBox = new TextBox();
		grid.setWidget(0, 1, serverIdTextBox);
		serverKeyTextBox = new TextBox();
		grid.setText(1, 0, "Server Key");
		grid.setWidget(1,1,serverKeyTextBox);
		grid.setText(2,0, "Comment");
		commentTextBox = new TextBox();
		grid.setWidget(2, 1, commentTextBox);
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button applyButton = new Button("Apply");
		applyButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				if (serverIdTextBox.getText() == null || serverIdTextBox.getText().length() == 0) {
					Window.alert("Please enter server ID");
					return;
				}
				if ( serverKeyTextBox.getText() == null || serverKeyTextBox.getText().length() == 0) {
					Window.alert("Please enter valid server key");
					return;
				}
				if ( commentTextBox.getText() != null && commentTextBox.getText().length() > 256) {
					Window.alert("Comment too long - please shorten it to < 256 chars.");
				}
				JSONObject jsonObject  = new JSONObject();
				jsonObject.put("PeerId", new JSONString(serverIdTextBox.getText()));
				jsonObject.put("key", new JSONString(serverKeyTextBox.getText()));
				if ( commentTextBox.getText() != null) {
					jsonObject.put("comment", new JSONString(commentTextBox.getText()));
				}
				Admin.getAdminService().addInboundPeer(jsonObject.toString(), inboundPeers);
			}});
		buttonPanel.add(applyButton);
		Button cancelButton = new Button("Cancel");
		cancelButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				inboundPeers.draw();				
			}});
		buttonPanel.add(cancelButton);
		
		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler( new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		buttonPanel.add(logoffButton);
		
		verticalPanel.add(buttonPanel);
		
	}

}
