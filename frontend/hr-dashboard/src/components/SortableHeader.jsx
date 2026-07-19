import React, { useState } from "react";

const SortableHeader = ({ label, onSort }) => {
  const [order, setOrder] = useState("asc");

  const handleSort = () => {
    const newOrder = order === "asc" ? "desc" : "asc";
    setOrder(newOrder);
    onSort(newOrder);
  };

  return (
    <th onClick={handleSort} style={{ cursor: "pointer" }}>
      {label} {order === "asc" ? "🔼" : "🔽"}
    </th>
  );
};

export default SortableHeader;
