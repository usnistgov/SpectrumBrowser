package gov.nist.spectrumbrowser.client;

import java.util.Set;

import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Tree;
import com.google.gwt.user.client.ui.TreeItem;

public class JSONViewer extends Composite {

	public JSONViewer(JSONObject jsonObject, String rootName) {
		Tree tree = new Tree();
		initWidget(tree);
		TreeItem rootItem = tree.addTextItem(rootName);
		populate(rootItem,jsonObject);
	}

	private void populate(TreeItem root, JSONObject jsonObject) {
		Set<String> keySet = jsonObject.keySet();
		for (String key : keySet) {
			JSONValue jsonValue = jsonObject.get(key);
			JSONString jsonString = jsonValue.isString();
			JSONNumber jsonNumber = jsonValue.isNumber();
			TreeItem treeItem =  root.addTextItem(key);
			if (jsonString != null) {
				String stringValue = jsonString.stringValue();
				treeItem.addTextItem(stringValue);
			} else if (jsonNumber != null ) {
				String stringValue = Double.toString(jsonNumber.doubleValue());
				treeItem.addTextItem(stringValue);
			} else if (jsonValue.isObject() != null) {
				populate(treeItem,jsonValue.isObject());
			}
		}

	}

}
